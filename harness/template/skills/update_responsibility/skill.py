import os
import re
import yaml
from datetime import datetime, timezone


_INTERVAL_RE = re.compile(r"^\s*\d+\s*[smhdw]\s*$", re.IGNORECASE)
_UPDATABLE_FIELDS = ('description', 'enabled', 'review_interval', 'last_reviewed')


def run(**input):
    name = input['name'].strip()
    rdir = 'entity/responsibilities'
    filepath = os.path.join(rdir, f"{name}.md")

    if not os.path.exists(filepath):
        return f"Responsibility {name!r} not found."

    if 'review_interval' in input:
        ri = input['review_interval']
        if ri is not None and not _INTERVAL_RE.match(str(ri)):
            return (
                f"Invalid review_interval {ri!r}: expected a value like "
                "'30m', '4h', '1d' (units: s/m/h/d/w)."
            )

    with open(filepath, 'r') as f:
        raw = f.read()

    if raw.startswith('---'):
        parts = raw.split('---', 2)
        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2].lstrip('\n') if len(parts) > 2 else ''
    else:
        fm = {}
        body = raw

    for field in _UPDATABLE_FIELDS:
        if field in input:
            fm[field] = input[field]

    if 'replace_content' in input:
        body = input['replace_content']

    # Any call to update_responsibility implies the entity touched it; bump
    # last_reviewed unless the caller passed an explicit value.
    if 'last_reviewed' not in input:
        fm['last_reviewed'] = datetime.now(timezone.utc).isoformat()

    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{body}")

    return f"Responsibility updated: {name}"
