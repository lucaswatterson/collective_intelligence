from pathlib import Path
from typing import Any

import yaml


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


def consolidated_session_stems(long_term_dir: Path) -> set[str]:
    stems: set[str] = set()
    if not long_term_dir.exists():
        return stems
    for f in long_term_dir.glob("*.md"):
        if f.name == "INDEX.md":
            continue
        try:
            fm, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for s in fm.get("source_sessions", []) or []:
            stems.add(str(s))
    return stems


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
