import os
import yaml
from datetime import datetime, timezone


def _resolve(tasks_dir, filename):
    filepath = os.path.join(tasks_dir, filename)
    if os.path.exists(filepath):
        return filepath, filename

    matches = [
        f for f in sorted(os.listdir(tasks_dir))
        if f.endswith('.md') and not f.startswith('.') and filename.lower() in f.lower()
    ]
    if len(matches) == 0:
        return None, f"No task found matching '{filename}'."
    if len(matches) > 1:
        return None, f"Multiple tasks match '{filename}':\n" + "\n".join(matches) + "\nBe more specific."
    return os.path.join(tasks_dir, matches[0]), matches[0]


def run(**input):
    filename = input['filename']
    tasks_dir = 'entity/tasks'

    if not os.path.exists(tasks_dir):
        return "No tasks directory found."

    filepath, resolved = _resolve(tasks_dir, filename)
    if filepath is None:
        return resolved  # error message

    with open(filepath, 'r') as f:
        raw = f.read()

    if raw.startswith('---'):
        parts = raw.split('---', 2)
        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2].lstrip('\n') if len(parts) > 2 else ''
    else:
        fm = {}
        body = raw

    # Apply frontmatter updates
    for field in ('title', 'status', 'priority', 'due', 'tags'):
        if field in input:
            fm[field] = input[field]

    # Apply body updates
    if 'replace_content' in input:
        body = input['replace_content']
    elif 'append_content' in input:
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        body = body.rstrip('\n') + f"\n\n---\n*Updated {ts}*\n\n{input['append_content']}\n"

    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
    new_content = f"---\n{fm_str}---\n\n{body}"

    with open(filepath, 'w') as f:
        f.write(new_content)

    return f"Task updated: {resolved}"
