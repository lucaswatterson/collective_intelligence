import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from harness.config import load_settings


CATEGORIES = ("user", "self", "collaboration", "lesson", "reference")


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except Exception:
        fm = {}
    return fm, parts[2]


def render_memory(fm: dict[str, Any], body: str) -> str:
    front = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    return "---\n" + front + "---\n\n" + body.strip() + "\n"


def rebuild_index(long_term_dir: Path, index_path: Path) -> None:
    if not long_term_dir.exists():
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("# Long-term memory index\n\n(empty)\n", encoding="utf-8")
        return

    by_category: dict[str, list[tuple[str, str, str]]] = {c: [] for c in CATEGORIES}
    uncategorized: list[tuple[str, str, str]] = []

    for f in sorted(long_term_dir.glob("*.md")):
        if f.name == "INDEX.md":
            continue
        try:
            fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        title = str(fm.get("title", f.stem))
        category = fm.get("category")
        gist = body.strip().splitlines()[0].strip() if body.strip() else ""
        if len(gist) > 120:
            gist = gist[:117] + "..."
        entry = (f.name, title, gist)
        if category in by_category:
            by_category[category].append(entry)
        else:
            uncategorized.append(entry)

    lines = ["# Long-term memory index", ""]
    total = sum(len(v) for v in by_category.values()) + len(uncategorized)
    if total == 0:
        lines.append("(empty)")
    else:
        for cat in CATEGORIES:
            entries = by_category[cat]
            if not entries:
                continue
            lines.append(f"## {cat}")
            lines.append("")
            for filename, title, gist in entries:
                suffix = f" — {gist}" if gist else ""
                lines.append(f"- `{filename}` — {title}{suffix}")
            lines.append("")
        if uncategorized:
            lines.append("## (uncategorized)")
            lines.append("")
            for filename, title, gist in uncategorized:
                suffix = f" — {gist}" if gist else ""
                lines.append(f"- `{filename}` — {title}{suffix}")
            lines.append("")

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def resolve_partial(dir_path: Path, filename: str, exclude: str = ".archive") -> Path | list[Path] | None:
    path = dir_path / filename
    if not path.suffix:
        path = path.with_suffix(".md")
    if path.exists():
        return path
    matches = [m for m in dir_path.glob(f"*{filename}*") if exclude not in str(m)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return sorted(matches)
    return None


def _create(input: dict, long_term_dir: Path, index_path: Path) -> str:
    title = input.get("title")
    content = input.get("content")
    category = input.get("category")
    if not title or not content or not category:
        return "create requires title, content, and category."
    if category not in CATEGORIES:
        return f"Invalid category: {category}. Must be one of {list(CATEGORIES)}."

    confidence = input.get("confidence", "medium")
    source_sessions = input.get("source_sessions") or []
    tags = input.get("tags") or []

    long_term_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_title = (
        "".join(c if c.isalnum() or c in "- " else " " for c in title)
        .strip()
        .replace(" ", "_")
        .lower()
    )
    filename = f"{timestamp}_{safe_title}.md"
    filepath = long_term_dir / filename

    fm = {
        "title": title,
        "category": category,
        "confidence": confidence,
        "source_sessions": list(source_sessions),
        "created": now.isoformat(),
        "updated": now.isoformat(),
        "tags": list(tags),
    }
    filepath.write_text(render_memory(fm, content), encoding="utf-8")
    rebuild_index(long_term_dir, index_path)
    return f"Memory saved: {filename}"


def _update(input: dict, long_term_dir: Path, index_path: Path) -> str:
    filename = input.get("filename")
    if not filename:
        return "update requires filename."
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
        fm["tags"] = list(input["tags"])
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
    rebuild_index(long_term_dir, index_path)
    return f"Memory updated: {memory_path.name}"


def _delete(input: dict, long_term_dir: Path, index_path: Path) -> str:
    filename = input.get("filename")
    if not filename:
        return "delete requires filename."
    if not long_term_dir.exists():
        return "No long-term memory directory found."

    result = resolve_partial(long_term_dir, filename)
    if result is None:
        return f"Memory not found: {filename}"
    if isinstance(result, list):
        names = [m.name for m in result]
        return "Multiple matches found:\n" + "\n".join(f"  - {n}" for n in names) + "\nPlease be more specific."

    memory_path = result
    archive_dir = long_term_dir / ".archive"
    archive_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archived_name = f"{memory_path.stem}_{timestamp}.md"
    archive_path = archive_dir / archived_name

    shutil.move(str(memory_path), str(archive_path))
    rebuild_index(long_term_dir, index_path)
    return f"Memory archived: {memory_path.name} → .archive/{archived_name}"


def _read(input: dict, long_term_dir: Path) -> str:
    filename = input.get("filename")
    if not filename:
        return "read requires filename."
    if not long_term_dir.exists():
        return "No long-term memory directory found."

    result = resolve_partial(long_term_dir, filename)
    if result is None:
        return f"Memory not found: {filename}"
    if isinstance(result, list):
        names = [m.name for m in result]
        return "Multiple matches found:\n" + "\n".join(f"  - {n}" for n in names) + "\nPlease be more specific."

    return result.read_text(encoding="utf-8")


def _unconsolidated(long_term_dir: Path, short_term_dir: Path) -> str:
    consolidated: set[str] = set()
    if long_term_dir.exists():
        for f in long_term_dir.glob("*.md"):
            if f.name == "INDEX.md":
                continue
            try:
                fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            for s in fm.get("source_sessions") or []:
                consolidated.add(str(s))

    if not short_term_dir.exists():
        return "No short-term sessions."

    stems = [f.stem for f in sorted(short_term_dir.glob("*.md")) if f.stem not in consolidated]
    if not stems:
        return "No unconsolidated sessions."
    return "\n".join(stems)


def _list(input: dict, long_term_dir: Path, index_path: Path) -> str:
    if not long_term_dir.exists():
        return "No long-term memories found."

    category_filter = input.get("category")
    tag_filter = input.get("tags") or []

    if not category_filter and not tag_filter:
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "No long-term memories found."

    rows = []
    for f in sorted(long_term_dir.glob("*.md")):
        if f.name == "INDEX.md":
            continue
        try:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if category_filter and fm.get("category") != category_filter:
            continue
        mem_tags = fm.get("tags") or []
        if tag_filter and not any(t in mem_tags for t in tag_filter):
            continue
        rows.append({
            "file": f.name,
            "title": fm.get("title", f.stem),
            "category": fm.get("category", "—"),
            "confidence": fm.get("confidence", "—"),
            "tags": mem_tags,
        })

    if not rows:
        parts = []
        if category_filter:
            parts.append(f"category={category_filter}")
        if tag_filter:
            parts.append(f"tags={tag_filter}")
        return f"No memories found (filters: {', '.join(parts)})."

    lines = []
    for r in rows:
        tags_str = ", ".join(r["tags"]) if r["tags"] else "—"
        lines.append(
            f"**{r['title']}**\n"
            f"  file: {r['file']}\n"
            f"  category: {r['category']}\n"
            f"  confidence: {r['confidence']}\n"
            f"  tags: {tags_str}"
        )

    return f"Found {len(rows)} memor{'y' if len(rows) == 1 else 'ies'}:\n\n" + "\n\n".join(lines)


def run(**input):
    action = input.get("action")
    if not action:
        return "action is required (create | update | delete | read | list)."

    settings = load_settings()
    long_term_dir = settings.long_term_dir
    index_path = settings.long_term_index_path

    if action == "create":
        return _create(input, long_term_dir, index_path)
    if action == "update":
        return _update(input, long_term_dir, index_path)
    if action == "delete":
        return _delete(input, long_term_dir, index_path)
    if action == "read":
        return _read(input, long_term_dir)
    if action == "list":
        return _list(input, long_term_dir, index_path)
    if action == "unconsolidated":
        return _unconsolidated(long_term_dir, settings.short_term_dir)

    return f"Unknown action: {action}. Must be one of create | update | delete | read | list | unconsolidated."
