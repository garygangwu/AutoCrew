import json

from openai import OpenAI

import config
import session
import skills
import tools


_client: OpenAI | None = None
_model: str = ""


def chat(user_message: str) -> str:
    global _client, _model
    cfg = config.load()
    _client = OpenAI()
    _model = cfg["model"]

    # Register the agent loop so spawn_agent can call it
    tools.set_agent_loop(run_sub_agent)

    # Build system prompt with available skills
    system_prompt = cfg["system_prompt"]
    skill_list = skills.list_skills()
    if skill_list:
        lines = ["\n\n## Available Skills\n"]
        lines.append("Call the `use_skill` tool with the skill name to load its full instructions before performing it.\n")
        for s in skill_list:
            lines.append(f"- **{s['name']}**: {s['description']}")
        system_prompt += "\n".join(lines)

    session.append("user", user_message)
    history = session.load()
    messages = [{"role": "system", "content": system_prompt}] + history

    reply = run_agent_loop(_client, _model, messages, tools.TOOL_SCHEMAS)

    session.append("assistant", reply)
    return reply


def run_sub_agent(messages: list, sub_tools: list) -> str:
    """Entry point for spawn_agent — runs a child agent loop with restricted tools."""
    return run_agent_loop(_client, _model, messages, sub_tools)


def _print_request(model: str, messages: list, iteration: int, tool_schemas: list | None = None) -> None:
    """Print the full request being sent to OpenAI."""
    schemas = tool_schemas or tools.TOOL_SCHEMAS
    print(f"\n{'='*60}")
    print(f"  REQUEST TO OPENAI (iteration {iteration})")
    print(f"  Model: {model}")
    print(f"  Messages: {len(messages)}")
    print(f"{'='*60}")
    for i, msg in enumerate(messages):
        role = msg["role"]
        print(f"\n--- [{i}] role: {role} ---")
        if "content" in msg and msg["content"]:
            content = msg["content"]
            if len(content) > 1000:
                print(content[:1000] + f"... ({len(content)} chars)")
            else:
                print(content)
        if "tool_calls" in msg:
            for tc in msg["tool_calls"]:
                fn = tc["function"]
                print(f"  -> tool_call: {fn['name']}({fn['arguments']})")
        if "tool_call_id" in msg:
            print(f"  (tool_call_id: {msg['tool_call_id']})")
    print(f"\n--- tools: {', '.join(t['function']['name'] for t in schemas)} ---")
    print(f"{'='*60}\n")


def _print_response(full_text: str, tool_call_list: list, iteration: int, thinking: str = "") -> None:
    """Pretty-print the response from OpenAI."""
    print(f"\n{'*'*60}")
    print(f"  RESPONSE FROM OPENAI (iteration {iteration})")
    print(f"{'*'*60}")

    if thinking:
        print(f"\n  💭 Thinking ({len(thinking)} chars):")
        print(f"  ┌{'─'*56}┐")
        for line in thinking.splitlines():
            if len(line) > 54:
                line = line[:51] + "..."
            print(f"  │ {line:<54} │")
        print(f"  └{'─'*56}┘")

    if full_text:
        print(f"\n  ✦ Text ({len(full_text)} chars):")
        print(f"  ┌{'─'*56}┐")
        for line in full_text.splitlines():
            if len(line) > 54:
                line = line[:51] + "..."
            print(f"  │ {line:<54} │")
        print(f"  └{'─'*56}┘")
    else:
        print(f"\n  ✦ Text: (none)")

    if tool_call_list:
        print(f"\n  ✦ Tool calls ({len(tool_call_list)}):")
        for i, tc in enumerate(tool_call_list):
            name = tc["function"]["name"]
            args_raw = tc["function"]["arguments"]
            try:
                args = json.dumps(json.loads(args_raw), indent=2)
            except (json.JSONDecodeError, TypeError):
                args = args_raw
            print(f"    [{i}] {name}()")
            print(f"        id: {tc['id']}")
            for arg_line in args.splitlines():
                print(f"        {arg_line}")
    else:
        print(f"\n  ✦ Tool calls: (none) — final response")

    print(f"{'*'*60}\n")


def run_agent_loop(client: OpenAI, model: str, messages: list, tool_schemas: list, max_iterations: int = 0) -> str:
    """Call the model in a loop, executing tool calls until it produces a final text reply.
    If max_iterations > 0, stop after that many iterations even if the model wants more tool calls."""
    # Reset skill-scoped runtime defaults for each top-level loop invocation.
    # This prevents cross-turn leakage in team mode while still allowing:
    # use_skill -> exec timeout defaults within a single loop.
    tools.clear_active_skill_context()

    iteration = 0
    while True:
        iteration += 1
        _print_request(model, messages, iteration, tool_schemas)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_schemas,
            stream=False
        )
        msg = response.choices[0].message
        full_text = msg.content or ""
        thinking = getattr(msg, "reasoning_content", None) or ""
        tool_call_list = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_call_list.append({
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        print('.'*60, flush=True)
        print("LLM Response:", flush=True)
        if thinking:
            print(f"\n  💭 Thinking:\n{thinking}", flush=True)
        if full_text:
            print(full_text, flush=True)
        print('.'*60, '\n', flush=True)

        _print_response(full_text, tool_call_list, iteration, thinking)

        # No tool calls — we're done
        if not tool_call_list:
            if full_text:
                print()
            return full_text

        # Build the assistant message with tool calls
        assistant_msg = {"role": "assistant", "tool_calls": []}
        if full_text:
            assistant_msg["content"] = full_text
        for tc in tool_call_list:
            assistant_msg["tool_calls"].append({
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"],
                },
            })
        messages.append(assistant_msg)

        # Execute each tool and append results
        for tc in tool_call_list:
            name = tc["function"]["name"]
            args_str = tc["function"]["arguments"]
            print(f"\n[tool: {name}]", flush=True)

            result = tools.run_tool(name, args_str)

            # Show a preview of the result
            preview = result[:200] + "..." if len(result) > 200 else result
            print(f"{preview}\n", flush=True)

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

        # Check iteration limit
        if max_iterations > 0 and iteration >= max_iterations:
            return full_text

        # Loop back — model will process tool results and either call more tools or reply
