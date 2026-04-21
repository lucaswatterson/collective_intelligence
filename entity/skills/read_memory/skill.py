from collective.config import load_settings
from collective.memory.long_term import resolve_partial


def run(**input):
    filename = input["filename"]
    long_term_dir = load_settings().long_term_dir

    if not long_term_dir.exists():
        return "No long-term memory directory found."

    result = resolve_partial(long_term_dir, filename)
    if result is None:
        return f"Memory not found: {filename}"
    if isinstance(result, list):
        names = [m.name for m in result]
        return "Multiple matches found:\n" + "\n".join(f"  - {n}" for n in names) + "\nPlease be more specific."

    return result.read_text(encoding="utf-8")
