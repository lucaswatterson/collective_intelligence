import os
import yaml


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
                })
                continue

        entries.append({
            'name': fm.get('name', filename[:-3]),
            'description': fm.get('description', ''),
        })

    entries.sort(key=lambda e: e['name'])

    lines = [f"- {e['name']}: {e['description']}" for e in entries]
    return "\n".join(lines)
