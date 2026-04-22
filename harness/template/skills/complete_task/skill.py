import os
import shutil
import yaml
from datetime import datetime, timezone


def run(**input):
    filename = input['filename']
    tasks_dir = 'entity/tasks'
    completed_dir = os.path.join(tasks_dir, '.completed')

    if not os.path.exists(tasks_dir):
        return "No tasks directory found."

    filepath = os.path.join(tasks_dir, filename)
    if not os.path.exists(filepath):
        matches = [
            f for f in sorted(os.listdir(tasks_dir))
            if f.endswith('.md') and not f.startswith('.') and filename.lower() in f.lower()
        ]
        if len(matches) == 0:
            return f"No task found matching '{filename}'."
        elif len(matches) > 1:
            return f"Multiple tasks match '{filename}':\n" + "\n".join(matches) + "\nBe more specific."
        filepath = os.path.join(tasks_dir, matches[0])
        filename = matches[0]

    with open(filepath, 'r') as f:
        raw = f.read()

    if raw.startswith('---'):
        parts = raw.split('---', 2)
        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2] if len(parts) > 2 else ''
    else:
        fm = {}
        body = raw

    fm['status'] = 'done'
    fm['completed'] = datetime.now(timezone.utc).isoformat()

    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
    new_content = f"---\n{fm_str}---\n{body}"

    with open(filepath, 'w') as f:
        f.write(new_content)

    os.makedirs(completed_dir, exist_ok=True)
    dest = os.path.join(completed_dir, filename)
    shutil.move(filepath, dest)

    return f"Task completed and moved to .completed/: {filename}"
