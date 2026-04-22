import yaml
from harness.config import load_settings


def run(**input):
    notes_dir = load_settings().entity_root / "notes"
    if not notes_dir.exists():
        return "No notes found."

    tag_filter = input.get("tags", [])

    notes = []
    for f in sorted(notes_dir.glob("*.md")):
        content = f.read_text()
        fm = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass

        note_tags = fm.get("tags", [])
        if tag_filter and not any(t in note_tags for t in tag_filter):
            continue

        notes.append({
            "file": f.name,
            "title": fm.get("title", f.stem),
            "created": fm.get("created", "—"),
            "tags": note_tags,
            "author": fm.get("author", "—"),
        })

    if not notes:
        msg = "No notes found."
        if tag_filter:
            msg += f" (filtered by tags: {tag_filter})"
        return msg

    lines = []
    for n in notes:
        tags_str = ", ".join(n["tags"]) if n["tags"] else "—"
        lines.append(
            f"**{n['title']}**\n"
            f"  file: {n['file']}\n"
            f"  created: {n['created']}\n"
            f"  tags: {tags_str}\n"
            f"  author: {n['author']}"
        )

    return f"Found {len(notes)} note(s):\n\n" + "\n\n".join(lines)
