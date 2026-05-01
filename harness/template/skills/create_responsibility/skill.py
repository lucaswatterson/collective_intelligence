import os
import re
import yaml
from datetime import datetime, timezone


_NAME_RE = re.compile(r"^[a-z0-9_]+$")


_INTERVAL_RE = re.compile(r"^\s*\d+\s*[smhdw]\s*$", re.IGNORECASE)


def run(**input):
    name = input['name'].strip()
    description = input['description'].strip()
    content = input['content']
    enabled = input.get('enabled', True)
    review_interval = input.get('review_interval')

    if not _NAME_RE.match(name):
        return f"Invalid name {name!r}: must be lowercase letters, digits, underscores."

    if review_interval is not None and not _INTERVAL_RE.match(str(review_interval)):
        return (
            f"Invalid review_interval {review_interval!r}: expected a value like "
            "'30m', '4h', '1d' (units: s/m/h/d/w)."
        )

    rdir = 'entity/responsibilities'
    os.makedirs(rdir, exist_ok=True)
    filepath = os.path.join(rdir, f"{name}.md")

    if os.path.exists(filepath):
        return f"Responsibility {name!r} already exists. Use update_responsibility or delete_responsibility first."

    now = datetime.now(timezone.utc).isoformat()
    fm = {
        'name': name,
        'description': description,
        'enabled': enabled,
        'review_interval': review_interval,
        'created': now,
        'last_reviewed': None,
    }
    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{content}\n")

    return f"Responsibility created: {name}"
