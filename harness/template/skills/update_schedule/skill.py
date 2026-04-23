import os
import re
from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml


_INTERVAL_RE = re.compile(r"^(\d+)([smhd])$")


class _QuotedStr(str):
    """Forces yaml.dump to emit the value as a single-quoted string.

    Needed for `at: "16:05"` — PyYAML otherwise parses the unquoted form as
    a base-60 sexagesimal int (16:05 → 965), which breaks round-trips.
    """


def _represent_quoted(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data), style="'")


yaml.add_representer(_QuotedStr, _represent_quoted)


def _coerce_at(value):
    """Return a QuotedStr HH:MM for an `at` value, handling PyYAML's
    sexagesimal int form (16:05 → 965) from previously-unquoted files."""
    if isinstance(value, int):
        hours, minutes = divmod(value, 60)
        return _QuotedStr(f"{hours:02d}:{minutes:02d}")
    return _QuotedStr(str(value))


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

    # If the existing file has `at`, always re-emit it quoted so that it
    # survives round-tripping through PyYAML (which treats unquoted HH:MM
    # as a base-60 int).
    if 'at' in fm and fm['at'] is not None:
        fm['at'] = _coerce_at(fm['at'])

    if 'interval' in input and 'at' in input:
        return "Provide either `interval` or `at`, not both."

    if 'interval' in input:
        interval = input['interval'].strip()
        m = _INTERVAL_RE.match(interval)
        if not m or int(m.group(1)) <= 0:
            return f"Invalid interval {interval!r}: expected e.g. '30s', '15m', '1h', '2d'."
        fm['interval'] = interval
        fm.pop('at', None)
        fm.pop('timezone', None)

    if 'at' in input:
        at = input['at'].strip()
        try:
            time.fromisoformat(at)
        except ValueError:
            return f"Invalid at {at!r}: expected 24-hour 'HH:MM' or 'HH:MM:SS', e.g. '16:05'."
        fm['at'] = _QuotedStr(at)
        fm.pop('interval', None)

    if 'timezone' in input:
        tz_value = input['timezone']
        if tz_value is None or str(tz_value).strip() == '':
            fm.pop('timezone', None)
        else:
            tz_name = str(tz_value).strip()
            try:
                ZoneInfo(tz_name)
            except ZoneInfoNotFoundError:
                return f"Invalid timezone {tz_name!r}: expected IANA name like 'America/Los_Angeles'."
            fm['timezone'] = tz_name

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
