import yaml
from datetime import datetime, timezone
from harness.config import load_settings


def run(**input):
    filename = input["filename"]
    notes_dir = load_settings().entity_root / "notes"

    if not notes_dir.exists():
        return "No notes directory found."

    note_path = notes_dir / filename
    if not note_path.suffix:
        note_path = note_path.with_suffix(".md")

    if not note_path.exists():
        matches = [
            m for m in notes_dir.glob(f"*{filename}*")
            if ".archive" not in str(m)
        ]
        if len(matches) == 1:
            note_path = matches[0]
        elif len(matches) > 1:
            names = [m.name for m in sorted(matches)]
            return "Multiple matches found:\n" + "\n".join(f"  - {n}" for n in names) + "\nPlease be more specific."
        else:
            return f"Note not found: {filename}"

    content = note_path.read_text()

    # Parse frontmatter
    fm = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm = {}
            body = parts[2]

    # Update frontmatter fields
    if "tags" in input:
        fm["tags"] = input["tags"]
    if "title" in input:
        fm["title"] = input["title"]

    # Update body
    append_content = input.get("append_content")
    replace_content = input.get("replace_content")

    if replace_content is not None:
        body = "\n" + replace_content.strip() + "\n"
    elif append_content:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        body = body.rstrip() + f"\n\n---\n*Updated {timestamp}*\n\n{append_content.strip()}\n"

    new_content = "---\n" + yaml.dump(fm, default_flow_style=False, sort_keys=False) + "---" + body
    note_path.write_text(new_content)

    return f"Note updated: {note_path.name}"
