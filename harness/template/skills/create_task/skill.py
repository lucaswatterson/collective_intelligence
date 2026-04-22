import os
import re
import yaml
from datetime import datetime, timezone


def run(**input):
    title = input['title']
    content = input['content']
    status = input.get('status', 'todo')
    priority = input.get('priority', 'medium')
    due = input.get('due')
    tags = input.get('tags', [])
    author = input.get('author', 'user')

    tasks_dir = 'entity/tasks'
    os.makedirs(tasks_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    created = now.isoformat()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')[:50]
    filename = f"{timestamp}_{slug}.md"
    filepath = os.path.join(tasks_dir, filename)

    frontmatter = {
        'title': title,
        'created': created,
        'status': status,
        'priority': priority,
        'tags': tags,
        'author': author,
    }
    if due:
        frontmatter['due'] = due

    fm_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    file_content = f"---\n{fm_str}---\n\n{content}\n"

    with open(filepath, 'w') as f:
        f.write(file_content)

    return f"Task created: {filename}"
