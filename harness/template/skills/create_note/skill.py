import yaml
from datetime import datetime, timezone
from harness.config import load_settings


def run(**input):
    title = input["title"]
    content = input["content"]
    tags = input.get("tags", [])
    author = input.get("author", "agent")

    notes_dir = load_settings().entity_root / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_title = (
        "".join(c if c.isalnum() or c in "- " else " " for c in title)
        .strip()
        .replace(" ", "_")
        .lower()
    )
    filename = f"{timestamp}_{safe_title}.md"
    filepath = notes_dir / filename

    fm = {"title": title, "created": now.isoformat(), "author": author, "tags": tags}
    frontmatter = "---\n" + yaml.dump(fm, default_flow_style=False, sort_keys=False) + "---\n"
    full_content = frontmatter + "\n" + content.strip() + "\n"

    filepath.write_text(full_content, encoding="utf-8")
    return f"Note saved: {filepath}"
