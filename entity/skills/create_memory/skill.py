from datetime import datetime, timezone

from harness.config import load_settings
from harness.memory.long_term import CATEGORIES, rebuild_index, render_memory


def run(**input):
    title = input["title"]
    content = input["content"]
    category = input["category"]
    confidence = input.get("confidence", "medium")
    source_sessions = input.get("source_sessions", []) or []
    tags = input.get("tags", []) or []

    if category not in CATEGORIES:
        return f"Invalid category: {category}. Must be one of {list(CATEGORIES)}."

    settings = load_settings()
    long_term_dir = settings.long_term_dir
    long_term_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_title = (
        "".join(c if c.isalnum() or c in "- " else " " for c in title)
        .strip()
        .replace(" ", "_")
        .lower()
    )
    filename = f"{timestamp}_{safe_title}.md"
    filepath = long_term_dir / filename

    fm = {
        "title": title,
        "category": category,
        "confidence": confidence,
        "source_sessions": source_sessions,
        "created": now.isoformat(),
        "updated": now.isoformat(),
        "tags": tags,
    }
    filepath.write_text(render_memory(fm, content), encoding="utf-8")

    rebuild_index(long_term_dir, settings.long_term_index_path)
    return f"Memory saved: {filename}"
