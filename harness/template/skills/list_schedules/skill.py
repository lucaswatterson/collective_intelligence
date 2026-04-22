import os
import re
import yaml
from datetime import datetime, timedelta, timezone


_INTERVAL_RE = re.compile(r"^(\d+)([smhd])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def _parse_interval(s):
    m = _INTERVAL_RE.match((s or "").strip())
    if not m:
        return None
    return timedelta(seconds=int(m.group(1)) * _UNIT_SECONDS[m.group(2)])


def _parse_dt(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(value))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def run(**input):
    schedules_dir = 'entity/schedules'
    if not os.path.isdir(schedules_dir):
        return "No schedules."

    files = sorted(
        f for f in os.listdir(schedules_dir)
        if f.endswith('.md') and not f.startswith('.')
    )
    if not files:
        return "No schedules."

    now = datetime.now(timezone.utc)
    lines = []
    for filename in files:
        path = os.path.join(schedules_dir, filename)
        with open(path, 'r') as f:
            raw = f.read()
        fm = {}
        if raw.startswith('---'):
            parts = raw.split('---', 2)
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                lines.append(f"- {filename}: (malformed frontmatter)")
                continue

        name = fm.get('name', filename[:-3])
        interval = fm.get('interval', '?')
        enabled = fm.get('enabled', True)
        last_run = _parse_dt(fm.get('last_run'))
        delta = _parse_interval(interval)

        if delta is None:
            next_fire = "(bad interval)"
        elif last_run is None:
            next_fire = "immediately"
        else:
            nf = last_run + delta
            next_fire = nf.isoformat() if nf > now else "overdue"

        last_run_s = last_run.isoformat() if last_run else "never"
        status = "enabled" if enabled else "disabled"
        lines.append(
            f"- {name}: every {interval} ({status}) | last_run={last_run_s} | next_fire={next_fire}"
        )

    return "\n".join(lines)
