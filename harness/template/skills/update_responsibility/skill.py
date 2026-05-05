import os
import yaml


_UPDATABLE_FIELDS = ('description',)


def run(**input):
    name = input['name'].strip()
    rdir = 'entity/responsibilities'
    filepath = os.path.join(rdir, f"{name}.md")

    if not os.path.exists(filepath):
        return f"Responsibility {name!r} not found."

    with open(filepath, 'r') as f:
        raw = f.read()

    if raw.startswith('---'):
        parts = raw.split('---', 2)
        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2].lstrip('\n') if len(parts) > 2 else ''
    else:
        fm = {}
        body = raw

    changed = False
    for field in _UPDATABLE_FIELDS:
        if field in input:
            fm[field] = input[field]
            changed = True

    if 'replace_content' in input:
        body = input['replace_content']
        changed = True

    if not changed:
        return f"No changes provided for {name!r}."

    fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(filepath, 'w') as f:
        f.write(f"---\n{fm_str}---\n\n{body}")

    return f"Responsibility updated: {name}"
