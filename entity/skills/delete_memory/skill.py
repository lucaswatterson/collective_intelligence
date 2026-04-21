import shutil
from datetime import datetime, timezone

from collective.config import load_settings
from collective.memory.long_term import rebuild_index, resolve_partial


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
    archive_dir = long_term_dir / ".archive"
    archive_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archived_name = f"{memory_path.stem}_{timestamp}.md"
    archive_path = archive_dir / archived_name

    shutil.move(str(memory_path), str(archive_path))

    rebuild_index(long_term_dir, settings.long_term_index_path)
    return f"Memory archived: {memory_path.name} → .archive/{archived_name}"
