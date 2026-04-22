from harness.config import load_settings


def run(**input):
    filename = input["filename"]
    notes_dir = load_settings().entity_root / "notes"

    if not notes_dir.exists():
        return "No notes directory found."

    # Ensure .md extension
    note_path = notes_dir / filename
    if not note_path.suffix:
        note_path = note_path.with_suffix(".md")

    if not note_path.exists():
        # Try partial match (exclude archive)
        matches = [
            m for m in notes_dir.glob(f"*{filename}*")
            if ".archive" not in str(m)
        ]
        if len(matches) == 1:
            note_path = matches[0]
        elif len(matches) > 1:
            names = [m.name for m in sorted(matches)]
            return f"Multiple matches found:\n" + "\n".join(f"  - {n}" for n in names) + "\nPlease be more specific."
        else:
            return f"Note not found: {filename}"

    return note_path.read_text()
