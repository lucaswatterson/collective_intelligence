import os
import yaml


def _sort_key(entry):
    # None (never reviewed) sorts before any timestamp.
    last_reviewed = entry['last_reviewed']
    return (last_reviewed is not None, last_reviewed or '', entry['name'])


def run(**input):
    rdir = 'entity/responsibilities'
    if not os.path.isdir(rdir):
        return "No responsibilities."

    files = sorted(
        f for f in os.listdir(rdir)
        if f.endswith('.md') and not f.startswith('.')
    )
    if not files:
        return "No responsibilities."

    entries = []
    for filename in files:
        path = os.path.join(rdir, filename)
        with open(path, 'r') as f:
            raw = f.read()
        fm = {}
        if raw.startswith('---'):
            parts = raw.split('---', 2)
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                entries.append({
                    'name': filename[:-3],
                    'description': '(malformed frontmatter)',
                    'enabled': False,
                    'last_reviewed': None,
                })
                continue

        entries.append({
            'name': fm.get('name', filename[:-3]),
            'description': fm.get('description', ''),
            'enabled': fm.get('enabled', True),
            'review_interval': fm.get('review_interval'),
            'last_reviewed': fm.get('last_reviewed'),
        })

    entries.sort(key=_sort_key)

    lines = []
    for e in entries:
        state = "enabled" if e['enabled'] else "disabled"
        last = e['last_reviewed'] or 'never'
        interval = e['review_interval'] or 'every tick'
        lines.append(
            f"- {e['name']} ({state}): {e['description']}\n"
            f"    review_interval={interval}  last_reviewed={last}"
        )

    return "\n".join(lines)
