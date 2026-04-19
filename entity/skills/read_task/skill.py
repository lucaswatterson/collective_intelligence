import os
import yaml


def run(**input):
    filename = input['filename']
    tasks_dir = 'entity/tasks'

    if not os.path.exists(tasks_dir):
        return "No tasks directory found."

    filepath = os.path.join(tasks_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()

    # Partial match
    matches = [
        f for f in sorted(os.listdir(tasks_dir))
        if f.endswith('.md') and not f.startswith('.') and filename.lower() in f.lower()
    ]

    if len(matches) == 0:
        return f"No task found matching '{filename}'."
    elif len(matches) > 1:
        return f"Multiple tasks match '{filename}':\n" + "\n".join(matches) + "\nBe more specific."

    filepath = os.path.join(tasks_dir, matches[0])
    with open(filepath, 'r') as f:
        return f.read()
