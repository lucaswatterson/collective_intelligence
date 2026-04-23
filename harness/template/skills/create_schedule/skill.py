import os
import re
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml


_INTERVAL_RE = re.compile(r"^(\d+)([smhd])$")
_NAME_RE = re.compile(r"^[a-z0-9_]+$")


class _QuotedStr(str):
    """Forces yaml.dump to emit the value as a single-quoted string.

    Needed for `at: "16:05"` — PyYAML otherwise parses the unquoted form as
    a base-60 sexagesimal int (16:05 → 965), which breaks round-trips.
    """


def _represent_quoted(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data), style="'")


yaml.add_representer(_QuotedStr, _represent_quoted)


def run(**input):
    name = input['name'].strip()
    task_title = input['task_title']
    content = input['content']
    task_priority = input.get('task_priority', 'medium')
    task_tags = input.get('task_tags', [])
    enabled = input.get('enabled', True)
    author = input.get('author', 'agent')

    interval = input.get('interval')
    at = input.get('at')
    tz_name = input.get('timezone')

    if not _NAME_RE.match(name):
        return f"Invalid name {name!r}: must be lowercase letters, digits, underscores."

    has_interval = interval is not None and str(interval).strip() != ''
    has_at = at is not None and str(at).strip() != ''
    if has_interval and has_at:
        return "Provide exactly one of `interval` or `at`, not both."
    if not has_interval and not has_at:
        return "Provide exactly one of `interval` or `at`."

    if has_interval:
        interval = interval.strip()
        m = _INTERVAL_RE.match(interval)
        if not m or int(m.group(1)) <= 0:
            return f"Invalid interval {interval!r}: expected e.g. '30s', '15m', '1h', '2d'."
    else:
        at = at.strip()
        try:
            time.fromisoformat(at)
        except ValueError:
            return f"Invalid at {at!r}: expected 24-hour 'HH:MM' or 'HH:MM:SS', e.g. '16:05'."
        if tz_name is not None and str(tz_name).strip() != '':
            tz_name = tz_name.strip()
            try:
                ZoneInfo(tz_name)
            except ZoneInfoNotFoundError:
                return f"Invalid timezone {tz_name!r}: expected IANA name like 'America/Los_Angeles'."
        else:
            tz_name = None

    schedules_dir = 'entity/schedules'
    os.makedirs(schedules_dir, exist_ok=True)
    filepath = os.path.join(schedules_dir, f"{name}.md")

    if os.path.exists(filepath):
        return f"Schedule {name!r} already exists. Use update_schedule or delete_schedule first."

    now = datetime.now(timezone.utc).isoformat()
    fm = {
        'name': name,
    }
    if has_interval:
        fm['interval'] = interval
    else:
        fm['at'] = _QuotedStr(at)
        if tz_name is not None:
            fm['timezone'] = tz_name
    fm.update({
        'enabled': enabled,
        'created': now,
        'last_run': None,
        'task_title': task_title,
        'task_priority': task_priority,
        'task_tags': task_tags,
        'author': author,
    })

    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{content}\n")

    if has_interval:
        return f"Schedule created: {name} (every {interval})"
    tz_suffix = f" {tz_name}" if tz_name else " (system local tz)"
    return f"Schedule created: {name} (daily at {at}{tz_suffix})"
