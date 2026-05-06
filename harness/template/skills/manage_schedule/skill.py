import os
import re

import yaml

from harness.runtime.guards import load_guards
from harness.runtime.schedule import parse_cron


SCHEDULE_PATH = 'entity/SCHEDULE.md'
RESPONSIBILITIES_DIR = 'entity/responsibilities'
NAME_RE = re.compile(r"^[a-z0-9_]+$")
INTERVAL_RE = re.compile(r"^\s*\d+\s*[smhdw]\s*$", re.IGNORECASE)


def _validate_guard(guard: object) -> str | None:
    if guard in (None, ''):
        return None
    guards = load_guards()
    if str(guard) not in guards:
        known = ", ".join(sorted(guards)) or "(none registered)"
        return (
            f"Unknown guard {guard!r}. Registered guards: {known}. "
            "Guards are pre-flight predicates that skip enqueueing when there's "
            "nothing to do (e.g. 'gmail_has_unread' skips manage_email when the "
            "inbox is empty)."
        )
    return None


def _load() -> tuple[list[dict], str]:
    """Return (entries, body). Empty defaults if the file doesn't exist."""
    if not os.path.exists(SCHEDULE_PATH):
        return ([], '')
    with open(SCHEDULE_PATH, 'r') as f:
        raw = f.read()
    if not raw.startswith('---'):
        return ([], raw)
    parts = raw.split('---', 2)
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip('\n') if len(parts) > 2 else ''
    entries = fm.get('entries') or []
    if not isinstance(entries, list):
        entries = []
    return (entries, body)


def _save(entries: list[dict], body: str) -> None:
    fm = {'entries': entries}
    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    os.makedirs(os.path.dirname(SCHEDULE_PATH) or '.', exist_ok=True)
    with open(SCHEDULE_PATH, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{body.rstrip()}\n" if body.strip() else f"---\n{fm_str}---\n")


def _validate_cadence(interval: object, cron: object) -> str | None:
    has_interval = interval not in (None, '')
    has_cron = cron not in (None, '')
    if has_interval and has_cron:
        return "Pass exactly one of interval or cron, not both."
    if not has_interval and not has_cron:
        return "Pass one of interval or cron."
    if has_interval and not INTERVAL_RE.match(str(interval)):
        return f"Invalid interval {interval!r}: expected '30m', '4h', '1d', etc. (units s/m/h/d/w)."
    if has_cron:
        try:
            parse_cron(str(cron))
        except Exception as exc:
            return f"Invalid cron {cron!r}: {exc}"
    return None


def _list(entries: list[dict]) -> str:
    known_guards = ", ".join(sorted(load_guards())) or "(none registered)"
    if not entries:
        return f"No schedule entries.\n\nAvailable guards: {known_guards}"
    lines = []
    for e in entries:
        cadence = e.get('interval') or e.get('cron') or '—'
        state = 'enabled' if e.get('enabled', True) else 'disabled'
        last = e.get('last_run') or 'never'
        guard = e.get('guard')
        row = (
            f"- {e.get('name', '?')} ({state}) → {e.get('responsibility', '?')}\n"
            f"    cadence={cadence}  last_run={last}"
        )
        if guard:
            row += f"  guard={guard}"
        lines.append(row)
    lines.append("")
    lines.append(f"Available guards: {known_guards}")
    return "\n".join(lines)


def _add(entries: list[dict], body: str, **input) -> str:
    name = (input.get('name') or '').strip()
    responsibility = (input.get('responsibility') or '').strip()
    if not name:
        return "Missing required field: name."
    if not NAME_RE.match(name):
        return f"Invalid name {name!r}: must be lowercase letters, digits, underscores."
    if not responsibility:
        return "Missing required field: responsibility."
    if any(e.get('name') == name for e in entries):
        return f"Schedule entry {name!r} already exists. Use action='update' or action='remove'."
    resp_path = os.path.join(RESPONSIBILITIES_DIR, f"{responsibility}.md")
    if not os.path.exists(resp_path):
        return f"Responsibility {responsibility!r} not found at {resp_path}. Create it first."
    interval = input.get('interval')
    cron = input.get('cron')
    err = _validate_cadence(interval, cron)
    if err:
        return err
    guard = input.get('guard')
    err = _validate_guard(guard)
    if err:
        return err
    entry: dict = {'name': name, 'responsibility': responsibility}
    if interval not in (None, ''):
        entry['interval'] = str(interval)
    else:
        entry['cron'] = str(cron)
    entry['enabled'] = bool(input.get('enabled', True))
    entry['last_run'] = None
    if guard not in (None, ''):
        entry['guard'] = str(guard)
    entries.append(entry)
    _save(entries, body)
    suffix = f" guard={entry['guard']}" if 'guard' in entry else ""
    return f"Schedule entry added: {name} → {responsibility} ({entry.get('interval') or entry.get('cron')}){suffix}"


def _update(entries: list[dict], body: str, **input) -> str:
    name = (input.get('name') or '').strip()
    if not name:
        return "Missing required field: name."
    target = next((e for e in entries if e.get('name') == name), None)
    if target is None:
        return f"Schedule entry {name!r} not found."

    if 'responsibility' in input:
        responsibility = (input['responsibility'] or '').strip()
        if not responsibility:
            return "responsibility cannot be empty."
        resp_path = os.path.join(RESPONSIBILITIES_DIR, f"{responsibility}.md")
        if not os.path.exists(resp_path):
            return f"Responsibility {responsibility!r} not found at {resp_path}."
        target['responsibility'] = responsibility

    cadence_touched = 'interval' in input or 'cron' in input
    if cadence_touched:
        new_interval = input.get('interval', target.get('interval'))
        new_cron = input.get('cron', target.get('cron'))
        # Caller passing one explicitly clears the other.
        if 'interval' in input and input['interval'] not in (None, ''):
            new_cron = None
        if 'cron' in input and input['cron'] not in (None, ''):
            new_interval = None
        err = _validate_cadence(new_interval, new_cron)
        if err:
            return err
        if new_interval not in (None, ''):
            target['interval'] = str(new_interval)
            target.pop('cron', None)
        else:
            target['cron'] = str(new_cron)
            target.pop('interval', None)

    if 'enabled' in input:
        target['enabled'] = bool(input['enabled'])

    if 'guard' in input:
        guard = input['guard']
        if guard in (None, ''):
            target.pop('guard', None)
        else:
            err = _validate_guard(guard)
            if err:
                return err
            target['guard'] = str(guard)

    _save(entries, body)
    return f"Schedule entry updated: {name}"


def _remove(entries: list[dict], body: str, **input) -> str:
    name = (input.get('name') or '').strip()
    if not name:
        return "Missing required field: name."
    before = len(entries)
    entries[:] = [e for e in entries if e.get('name') != name]
    if len(entries) == before:
        return f"Schedule entry {name!r} not found."
    _save(entries, body)
    return f"Schedule entry removed: {name}"


def run(**input):
    action = input.get('action')
    if action not in ('list', 'add', 'update', 'remove'):
        return "Missing or invalid action. Use one of: list, add, update, remove."
    entries, body = _load()
    if action == 'list':
        return _list(entries)
    if action == 'add':
        return _add(entries, body, **input)
    if action == 'update':
        return _update(entries, body, **input)
    if action == 'remove':
        return _remove(entries, body, **input)
    return "Unreachable."
