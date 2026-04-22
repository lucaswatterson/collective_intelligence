import os
import re
import yaml
from datetime import datetime, timezone


_INTERVAL_RE = re.compile(r"^(\d+)([smhd])$")
_NAME_RE = re.compile(r"^[a-z0-9_]+$")


def run(**input):
    name = input['name'].strip()
    interval = input['interval'].strip()
    task_title = input['task_title']
    content = input['content']
    task_priority = input.get('task_priority', 'medium')
    task_tags = input.get('task_tags', [])
    enabled = input.get('enabled', True)
    author = input.get('author', 'agent')

    if not _NAME_RE.match(name):
        return f"Invalid name {name!r}: must be lowercase letters, digits, underscores."
    m = _INTERVAL_RE.match(interval)
    if not m or int(m.group(1)) <= 0:
        return f"Invalid interval {interval!r}: expected e.g. '30s', '15m', '1h', '2d'."

    schedules_dir = 'entity/schedules'
    os.makedirs(schedules_dir, exist_ok=True)
    filepath = os.path.join(schedules_dir, f"{name}.md")

    if os.path.exists(filepath):
        return f"Schedule {name!r} already exists. Use update_schedule or delete_schedule first."

    now = datetime.now(timezone.utc).isoformat()
    fm = {
        'name': name,
        'interval': interval,
        'enabled': enabled,
        'created': now,
        'last_run': None,
        'task_title': task_title,
        'task_priority': task_priority,
        'task_tags': task_tags,
        'author': author,
    }

    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{content}\n")

    return f"Schedule created: {name} (every {interval})"
