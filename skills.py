import glob
import os
import re

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> dict:
    """Extract selected frontmatter keys (simple parser, no PyYAML needed)."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        for key in ("name", "description", "exec_timeout_sec"):
            if line.startswith(f"{key}:"):
                result[key] = line[len(key) + 1:].strip()
    return result


def list_skills() -> list[dict]:
    """Return list of {'name': ..., 'description': ...} for all discovered skills."""
    skills = []
    for path in sorted(glob.glob(os.path.join(SKILLS_DIR, "*", "SKILL.md"))):
        try:
            with open(path) as f:
                text = f.read()
        except OSError:
            continue
        meta = _parse_frontmatter(text)
        if "name" in meta:
            skills.append({
                "name": meta["name"],
                "description": meta.get("description", ""),
            })
    return skills


def load_skill(name: str) -> str:
    """Return the full SKILL.md content for the given skill name, with {baseDir} resolved."""
    skill_dir = os.path.join(SKILLS_DIR, name)
    path = os.path.join(skill_dir, "SKILL.md")
    try:
        with open(path) as f:
            content = f.read()
        return content.replace("{baseDir}", skill_dir)
    except FileNotFoundError:
        return f"Error: skill not found: {name}"


def skill_exec_timeout_sec(name: str) -> int | None:
    """Return skill-specific default exec timeout in seconds, or None if not set/invalid."""
    path = os.path.join(SKILLS_DIR, name, "SKILL.md")
    try:
        with open(path) as f:
            text = f.read()
    except FileNotFoundError:
        return None
    except OSError:
        return None

    meta = _parse_frontmatter(text)
    raw = meta.get("exec_timeout_sec")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None
