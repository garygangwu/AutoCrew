"""Role catalog for multi-agent teams."""

ROLE_CATALOG = {
    "orchestrator": {
        "name": "orchestrator",
        "description": "Coordinates the team, delegates tasks, and declares when work is done.",
        "system_prompt": (
            "You are the orchestrator of a multi-agent team. Your job is to:\n"
            "1. Read messages from other agents to understand progress\n"
            "2. Post clear directives telling agents what to do next\n"
            "3. Identify when all work is complete and call declare_done with a summary\n\n"
            "Do NOT do research or write code yourself — delegate to the right agents.\n"
            "Be concise in your messages. Focus on coordination."
        ),
        "allowed_tools": [
            "read_file", "web_fetch",
            "post_message", "read_messages", "read_artifacts", "declare_done",
        ],
        "can_spawn": False,
    },
    "researcher": {
        "name": "researcher",
        "description": "Gathers information from the web, files, and documents.",
        "system_prompt": (
            "You are a researcher agent. Your job is to find information, read documents, "
            "and share your findings with the team via post_message.\n"
            "Always post a summary of what you found so other agents can use it."
        ),
        "allowed_tools": [
            "exec", "read_file", "web_fetch", "pdf_fetch", "use_skill",
            "post_message", "read_messages", "read_artifacts",
        ],
        "can_spawn": False,
    },
    "coder": {
        "name": "coder",
        "description": "Writes code, runs tests, and produces software artifacts.",
        "system_prompt": (
            "You are a coder agent. Your job is to write code, run tests, and fix bugs.\n"
            "Save your code to the team artifacts directory when instructed.\n"
            "Post progress updates and results to the message board."
        ),
        "allowed_tools": [
            "exec", "read_file", "write_file", "use_skill",
            "post_message", "read_messages", "read_artifacts", "spawn_agent",
        ],
        "can_spawn": True,
    },
    "reviewer": {
        "name": "reviewer",
        "description": "Reviews artifacts for correctness, quality, and completeness.",
        "system_prompt": (
            "You are a reviewer agent. Your job is to review code, documents, and other artifacts.\n"
            "Read artifacts, check for issues, and post your feedback to the message board.\n"
            "Be specific about what needs to change."
        ),
        "allowed_tools": [
            "exec", "read_file",
            "post_message", "read_messages", "read_artifacts",
        ],
        "can_spawn": False,
    },
    "writer": {
        "name": "writer",
        "description": "Produces documentation, reports, and summaries.",
        "system_prompt": (
            "You are a writer agent. Your job is to produce well-written documents, "
            "reports, and summaries.\n"
            "Save your output to the team artifacts directory.\n"
            "Post updates about your progress to the message board."
        ),
        "allowed_tools": [
            "read_file", "write_file", "web_fetch", "use_skill",
            "post_message", "read_messages", "read_artifacts",
        ],
        "can_spawn": False,
    },
}


def get_role(name: str) -> dict | None:
    """Return a role definition by name, or None if not found."""
    return ROLE_CATALOG.get(name)


def catalog_summary() -> str:
    """Return a formatted summary of all roles for the meta-orchestrator prompt."""
    lines = ["Available roles:"]
    for role in ROLE_CATALOG.values():
        tools_str = ", ".join(
            t for t in role["allowed_tools"]
            if t not in ("post_message", "read_messages", "read_artifacts", "declare_done")
        )
        lines.append(f"- {role['name']}: {role['description']} [tools: {tools_str}]")
    return "\n".join(lines)
