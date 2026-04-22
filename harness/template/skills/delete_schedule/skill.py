import os
import shutil
from datetime import datetime, timezone


def run(**input):
    name = input['name'].strip()
    schedules_dir = 'entity/schedules'
    archive_dir = os.path.join(schedules_dir, '.archive')

    filepath = os.path.join(schedules_dir, f"{name}.md")
    if not os.path.exists(filepath):
        return f"Schedule {name!r} not found."

    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    dest_filename = f"{name}_{ts}.md"
    dest = os.path.join(archive_dir, dest_filename)
    shutil.move(filepath, dest)

    return f"Schedule archived: {dest_filename}"
