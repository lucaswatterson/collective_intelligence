"""Reset the entity to a fresh (unborn) state.

Clears IDENTITY.md and removes all files under entity/{files,memory,public,tasks}.
Skills are preserved — they are harness/development artifacts, not entity state.
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
ENTITY_ROOT = REPO_ROOT / "entity"

CLEAR_DIRS = [
    ENTITY_ROOT / "files",
    ENTITY_ROOT / "memory" / "short_term",
    ENTITY_ROOT / "memory" / "long_term",
    ENTITY_ROOT / "public",
    ENTITY_ROOT / "tasks",
]


def reset() -> None:
    identity = ENTITY_ROOT / "IDENTITY.md"
    if identity.exists():
        identity.write_text("", encoding="utf-8")
        print(f"Cleared {identity.relative_to(REPO_ROOT)}")

    for d in CLEAR_DIRS:
        if not d.exists():
            continue
        removed = 0
        for item in d.iterdir():
            if item.is_file():
                item.unlink()
                removed += 1
            elif item.is_dir():
                shutil.rmtree(item)
                removed += 1
        if removed:
            print(f"Removed {removed} item(s) from {d.relative_to(REPO_ROOT)}/")

    print("Entity reset. Skills preserved.")


if __name__ == "__main__":
    reset()
