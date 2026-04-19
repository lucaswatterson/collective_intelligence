import shutil
from datetime import datetime, timezone
from collective.config import load_settings


def run(**input):
    filename = input["filename"]
    notes_dir = load_settings().entity_root / "notes"
    archive_dir = notes_dir / ".archive"

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

    archive_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archived_name = f"{note_path.stem}_{timestamp}.md"
    archive_path = archive_dir / archived_name

    shutil.move(str(note_path), str(archive_path))

    return f"Note archived: {note_path.name} → .archive/{archived_name}"
