import os
import re
import yaml
from datetime import datetime, timezone


_NAME_RE = re.compile(r"^[a-z0-9_]+$")


def run(**input):
    name = input['name'].strip()
    description = input['description'].strip()
    content = input['content']

    if not _NAME_RE.match(name):
        return f"Invalid name {name!r}: must be lowercase letters, digits, underscores."

    rdir = 'entity/responsibilities'
    os.makedirs(rdir, exist_ok=True)
    filepath = os.path.join(rdir, f"{name}.md")

    if os.path.exists(filepath):
        return f"Responsibility {name!r} already exists. Use update_responsibility or delete_responsibility first."

    now = datetime.now(timezone.utc).isoformat()
    fm = {
        'name': name,
        'description': description,
        'created': now,
    }
    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{content}\n")

    return (
        f"Responsibility created: {name}. To make it run on a cadence, add it to "
        f"the schedule with `manage_schedule` (action='add')."
    )
