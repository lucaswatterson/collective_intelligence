import os
import re
from datetime import datetime, timezone


def slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "_", slug)
    slug = re.sub(r"-+", "_", slug)
    return slug[:60]


def run(**input):
    title = input["title"]
    content = input["content"]
    tags = input.get("tags", [])

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    slug = slugify(title)
    filename = f"{date_str}_{slug}.md"

    notes_dir = os.path.join("entity", "notes")
    os.makedirs(notes_dir, exist_ok=True)

    filepath = os.path.join(notes_dir, filename)

    tag_list = "\n".join(f"  - {tag}" for tag in tags) if tags else ""
    tags_block = f"tags:\n{tag_list}" if tag_list else "tags: []"

    frontmatter = f"""---
title: "{title}"
date: {timestamp}
{tags_block}
---"""

    full_content = f"{frontmatter}\n\n{content}\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    return f"Note saved: {filepath}"
