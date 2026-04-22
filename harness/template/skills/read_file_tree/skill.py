import os

ENTITY_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')


def _human_size(nbytes: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if nbytes < 1024:
            return f"{nbytes:.0f} {unit}" if unit == 'B' else f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def _build_tree(
    abs_path: str,
    prefix: str,
    max_depth: int,
    current_depth: int,
    show_hidden: bool,
    show_sizes: bool,
    lines: list,
) -> None:
    if max_depth != -1 and current_depth > max_depth:
        return

    try:
        entries = list(os.scandir(abs_path))
    except PermissionError:
        lines.append(f"{prefix}[permission denied]")
        return

    # Filter hidden unless requested
    if not show_hidden:
        entries = [e for e in entries if not e.name.startswith('.')]

    # Sort: directories first, then files, both alphabetical
    dirs = sorted([e for e in entries if e.is_dir(follow_symlinks=False)], key=lambda e: e.name.lower())
    files = sorted([e for e in entries if not e.is_dir(follow_symlinks=False)], key=lambda e: e.name.lower())
    all_entries = dirs + files
    total = len(all_entries)

    for idx, entry in enumerate(all_entries):
        is_last = idx == total - 1
        connector = '└── ' if is_last else '├── '
        child_prefix = prefix + ('    ' if is_last else '│   ')

        if entry.is_dir(follow_symlinks=False):
            lines.append(f"{prefix}{connector}{entry.name}/")
            _build_tree(
                entry.path,
                child_prefix,
                max_depth,
                current_depth + 1,
                show_hidden,
                show_sizes,
                lines,
            )
        else:
            if show_sizes:
                try:
                    size = entry.stat().st_size
                    size_str = f"  ({_human_size(size)})"
                except OSError:
                    size_str = ""
            else:
                size_str = ""
            lines.append(f"{prefix}{connector}{entry.name}{size_str}")


def run(**input):
    rel_path = input.get('path', '') or ''
    max_depth = input.get('max_depth', -1)
    if max_depth is None:
        max_depth = -1
    show_hidden = input.get('show_hidden', False)
    show_sizes = input.get('show_sizes', True)

    entity_root = os.path.normpath(ENTITY_ROOT)

    if rel_path:
        abs_start = os.path.normpath(os.path.join(entity_root, rel_path))
    else:
        abs_start = entity_root

    # Safety: prevent escaping entity root
    if not abs_start.startswith(entity_root):
        return "Error: path escapes entity root."

    if not os.path.isdir(abs_start):
        return f"Error: '{rel_path}' is not a directory within entity/."

    display_root = rel_path if rel_path else 'entity/'
    lines = [f"{display_root}"]
    _build_tree(abs_start, '', max_depth, 0, show_hidden, show_sizes, lines)

    if len(lines) == 1:
        lines.append("  (empty)")

    return '\n'.join(lines)
