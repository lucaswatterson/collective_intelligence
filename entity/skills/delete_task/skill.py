import os
import shutil
from datetime import datetime, timezone


def run(**input):
    filename = input['filename']
    tasks_dir = 'entity/tasks'
    archive_dir = os.path.join(tasks_dir, '.archive')

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

    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    stem = filename.replace('.md', '')
    dest_filename = f"{stem}_{ts}.md"
    dest = os.path.join(archive_dir, dest_filename)
    shutil.move(filepath, dest)

    return f"Task archived: {dest_filename}"
