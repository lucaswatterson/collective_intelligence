import shutil

from harness.config import load_settings
from harness.memory.long_term import resolve_partial


def run(**input):
    session = input["session"]
    settings = load_settings()
    short_term_dir = settings.short_term_dir
    archive_dir = settings.short_term_archive_dir

    name = session if session.endswith(".md") else f"{session}.md"

    archive_dir.mkdir(parents=True, exist_ok=True)

    if (archive_dir / name).exists() and not (short_term_dir / name).exists():
        return f"Session already archived: {name}"

    if not short_term_dir.exists():
        return "No short-term memory directory found."

    result = resolve_partial(short_term_dir, session, exclude="__never__")
    if result is None:
        if (archive_dir / name).exists():
            return f"Session already archived: {name}"
        return f"Session not found: {session}"
    if isinstance(result, list):
        names = [m.name for m in result]
        return "Multiple matches found:\n" + "\n".join(f"  - {n}" for n in names) + "\nPlease be more specific."

    session_path = result
    dest = archive_dir / session_path.name
    if dest.exists():
        return f"Session already archived: {session_path.name}"

    shutil.move(str(session_path), str(dest))
    return f"Session archived: {session_path.name}"
