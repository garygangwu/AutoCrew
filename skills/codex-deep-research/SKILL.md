---
name: codex-deep-research
description: Research a topic with Codex CLI and produce a concise evidence-backed summary. Use when the user asks for deep research, literature review, market/technical landscape analysis, source-backed findings, or key takeaways with citations.
metadata:
  { "autocrew": { "emoji": "🔎", "requires": { "bins": ["codex"] } } }
---

# Codex Deep Research

Use this skill to run structured research through `codex exec`, then summarize results with citations and key takeaways.
Always include `--skip-git-repo-check` for research-only runs.

## Primary command

```bash
codex exec --skip-git-repo-check "Research topic: <TOPIC>. Summarize findings with citations and key takeaways."
```

## Recommended workflow

1. Define scope in one sentence (topic, target audience, and depth).
2. Run `codex exec --skip-git-repo-check` with a focused prompt.
3. If results are broad, run follow-up passes for subtopics.
4. Merge findings and remove duplicates.
5. Return a final summary with citations and clear takeaways.

## Prompt template

```text
Research topic: <TOPIC>.
Context: <OPTIONAL CONTEXT OR GOAL>.
Depth: <BASIC|MEDIUM|DEEP>.
Timeframe: <OPTIONAL, e.g. last 2 years>.
Output requirements:
- Summarize findings with citations.
- Highlight consensus vs disagreement.
- Include risks, assumptions, and unknowns.
- End with key takeaways.
```

## Follow-up commands (optional)

Use these when you need tighter coverage:

```bash
codex exec --skip-git-repo-check "Research topic: <SUBTOPIC A>. Summarize findings with citations and key takeaways."
codex exec --skip-git-repo-check "Research topic: <SUBTOPIC B>. Summarize findings with citations and key takeaways."
```

## Response format

Return results in this structure:

```markdown
## Topic
<short restatement>

## Findings
- <finding 1> [citation]
- <finding 2> [citation]

## Key takeaways
- <takeaway 1>
- <takeaway 2>

## Risks and unknowns
- <risk/assumption>
```

## Quality checks

- Keep claims tied to at least one citation.
- Distinguish established facts from speculation.
- Call out stale or conflicting evidence.
- If citations are weak, say so and recommend next research steps.
