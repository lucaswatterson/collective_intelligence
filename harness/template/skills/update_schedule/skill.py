import os
import re
import yaml


_INTERVAL_RE = re.compile(r"^(\d+)([smhd])$")


def run(**input):
    name = input['name'].strip()
    schedules_dir = 'entity/schedules'
    filepath = os.path.join(schedules_dir, f"{name}.md")

    if not os.path.exists(filepath):
        return f"Schedule {name!r} not found."

    with open(filepath, 'r') as f:
        raw = f.read()

    if not raw.startswith('---'):
        return f"Schedule {name!r} is malformed (no frontmatter)."
    parts = raw.split('---', 2)
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip('\n') if len(parts) > 2 else ''

    if 'interval' in input:
        interval = input['interval'].strip()
        m = _INTERVAL_RE.match(interval)
        if not m or int(m.group(1)) <= 0:
            return f"Invalid interval {interval!r}: expected e.g. '30s', '15m', '1h', '2d'."
        fm['interval'] = interval

    for field in ('enabled', 'task_title', 'task_priority', 'task_tags'):
        if field in input:
            fm[field] = input[field]

    if 'content' in input:
        body = input['content']
        if not body.endswith('\n'):
            body += '\n'

    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{body}")

    return f"Schedule updated: {name}"
