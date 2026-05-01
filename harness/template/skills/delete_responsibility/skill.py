import os
import shutil
from datetime import datetime, timezone


def run(**input):
    name = input['name'].strip()
    rdir = 'entity/responsibilities'
    archive_dir = os.path.join(rdir, '.archive')

    filepath = os.path.join(rdir, f"{name}.md")
    if not os.path.exists(filepath):
        return f"Responsibility {name!r} not found."

    os.makedirs(archive_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    dest_filename = f"{name}_{ts}.md"
    dest = os.path.join(archive_dir, dest_filename)
    shutil.move(filepath, dest)

    return f"Responsibility archived: {dest_filename}"
