import os


def run(**input):
    name = input['name'].strip()
    rdir = 'entity/responsibilities'
    filepath = os.path.join(rdir, f"{name}.md")

    if not os.path.exists(filepath):
        return f"Responsibility {name!r} not found."

    with open(filepath, 'r') as f:
        return f.read()
