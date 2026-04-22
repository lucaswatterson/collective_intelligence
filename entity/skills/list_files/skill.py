import os
import fnmatch
import datetime


def run(**input):
    entity_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rel_path   = input.get("path", "").strip().lstrip("/")
    pattern    = input.get("pattern", "*")
    recursive  = input.get("recursive", False)

    target = os.path.normpath(os.path.join(entity_dir, rel_path))

    # Safety: must stay inside entity_dir
    if not target.startswith(entity_dir):
        return "Error: path escapes the entity directory."

    if not os.path.exists(target):
        return f"Error: '{rel_path}' does not exist."

    if not os.path.isdir(target):
        return f"Error: '{rel_path}' is not a directory."

    entries = []

    if recursive:
        for dirpath, dirnames, filenames in os.walk(target):
            # Skip hidden directories
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            for fname in filenames:
                if fnmatch.fnmatch(fname, pattern):
                    full = os.path.join(dirpath, fname)
                    rel  = os.path.relpath(full, target)
                    entries.append((rel, full))
    else:
        try:
            for fname in os.listdir(target):
                if fnmatch.fnmatch(fname, pattern):
                    full = os.path.join(target, fname)
                    if os.path.isfile(full):
                        entries.append((fname, full))
        except PermissionError as e:
            return f"Error: {e}"

    if not entries:
        return f"No files matching '{pattern}' in '{rel_path}'."

    entries.sort(key=lambda e: e[0].lower())

    # Format output
    lines = [f"{'NAME':<45} {'SIZE':>8}  MODIFIED"]
    lines.append("─" * 72)
    for name, full in entries:
        stat  = os.stat(full)
        size  = stat.st_size
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        if size < 1024:
            size_str = f"{size}B"
        elif size < 1024 ** 2:
            size_str = f"{size/1024:.1f}K"
        else:
            size_str = f"{size/1024**2:.1f}M"
        lines.append(f"{name:<45} {size_str:>8}  {mtime}")

    lines.append("─" * 72)
    lines.append(f"{len(entries)} file(s) in '{rel_path}'")
    return "\n".join(lines)
