from datetime import datetime, timezone

from collective.config import load_settings
from collective.memory.long_term import (
    CATEGORIES,
    parse_frontmatter,
    rebuild_index,
    render_memory,
    resolve_partial,
)


def run(**input):
    filename = input["filename"]
    settings = load_settings()
    long_term_dir = settings.long_term_dir

    if not long_term_dir.exists():
        return "No long-term memory directory found."

    result = resolve_partial(long_term_dir, filename)
    if result is None:
        return f"Memory not found: {filename}"
    if isinstance(result, list):
        names = [m.name for m in result]
        return "Multiple matches found:\n" + "\n".join(f"  - {n}" for n in names) + "\nPlease be more specific."

    memory_path = result
    fm, body = parse_frontmatter(memory_path.read_text(encoding="utf-8"))

    changed = False

    if "title" in input:
        fm["title"] = input["title"]
        changed = True
    if "category" in input:
        if input["category"] not in CATEGORIES:
            return f"Invalid category: {input['category']}. Must be one of {list(CATEGORIES)}."
        fm["category"] = input["category"]
        changed = True
    if "confidence" in input:
        fm["confidence"] = input["confidence"]
        changed = True
    if "tags" in input:
        fm["tags"] = input["tags"]
        changed = True
    if "add_source_sessions" in input:
        current = list(fm.get("source_sessions") or [])
        for s in input["add_source_sessions"]:
            if s not in current:
                current.append(s)
        fm["source_sessions"] = current
        changed = True

    replace_content = input.get("replace_content")
    append_content = input.get("append_content")
    if replace_content is not None:
        body = "\n" + replace_content.strip() + "\n"
        changed = True
    elif append_content:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        body = body.rstrip() + f"\n\n---\n*Updated {ts}*\n\n{append_content.strip()}\n"
        changed = True

    if not changed:
        return "No updates provided. Pass at least one mutating field."

    fm["updated"] = datetime.now(timezone.utc).isoformat()
    memory_path.write_text(render_memory(fm, body), encoding="utf-8")

    rebuild_index(long_term_dir, settings.long_term_index_path)
    return f"Memory updated: {memory_path.name}"
