from harness.config import load_settings
from harness.memory.long_term import parse_frontmatter


def run(**input):
    settings = load_settings()
    long_term_dir = settings.long_term_dir
    if not long_term_dir.exists():
        return "No long-term memories found."

    category_filter = input.get("category")
    tag_filter = input.get("tags") or []

    if not category_filter and not tag_filter:
        if settings.long_term_index_path.exists():
            return settings.long_term_index_path.read_text(encoding="utf-8")
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
