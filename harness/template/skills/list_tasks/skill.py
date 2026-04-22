import os
import yaml


def run(**input):
    status_filter = input.get('status')
    tags_filter = input.get('tags', [])
    priority_filter = input.get('priority')

    tasks_dir = 'entity/tasks'
    if not os.path.exists(tasks_dir):
        return "No tasks directory found."

    results = []
    for filename in sorted(os.listdir(tasks_dir)):
        if not filename.endswith('.md') or filename.startswith('.'):
            continue
        filepath = os.path.join(tasks_dir, filename)
        with open(filepath, 'r') as f:
            raw = f.read()

        if raw.startswith('---'):
            parts = raw.split('---', 2)
            if len(parts) >= 2:
                try:
                    fm = yaml.safe_load(parts[1])
                except Exception:
                    continue
            else:
                continue
        else:
            continue

        if status_filter and fm.get('status') != status_filter:
            continue
        if priority_filter and fm.get('priority') != priority_filter:
            continue
        if tags_filter:
            task_tags = fm.get('tags', [])
            if not any(t in task_tags for t in tags_filter):
                continue

        results.append({
            'filename': filename,
            'title': fm.get('title', '(untitled)'),
            'status': fm.get('status', '?'),
            'priority': fm.get('priority', '?'),
            'due': fm.get('due'),
            'tags': fm.get('tags', []),
            'created': fm.get('created', '?'),
        })

    if not results:
        return "No tasks found matching criteria."

    lines = []
    for r in results:
        due_str = f" | due: {r['due']}" if r['due'] else ""
        tags_str = f" | [{', '.join(r['tags'])}]" if r['tags'] else ""
        lines.append(
            f"[{r['priority'].upper()}] [{r['status']}] {r['title']}{due_str}{tags_str}\n  → {r['filename']}"
        )

    return f"{len(results)} task(s):\n\n" + "\n".join(lines)
