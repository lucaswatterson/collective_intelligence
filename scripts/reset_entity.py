"""Reset the entity to a fresh (unborn) state.

Clears IDENTITY.md, self_image.txt, and worker.log, and removes all files under
entity/{files,images,memory,public,tasks}.
Skills are preserved — they are harness/development artifacts, not entity state.
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENTITY_ROOT = REPO_ROOT / "entity"

CLEAR_DIRS = [
    ENTITY_ROOT / "files",
    ENTITY_ROOT / "images",
    ENTITY_ROOT / "memory" / "short_term",
    ENTITY_ROOT / "memory" / "long_term",
    ENTITY_ROOT / "memory" / "short_term_archive",
    ENTITY_ROOT / "notes",
    ENTITY_ROOT / "public",
    ENTITY_ROOT / "tasks",
    ENTITY_ROOT / "work",
]

CLEAR_FILES = [
    ENTITY_ROOT / "IDENTITY.md",
    ENTITY_ROOT / "self_image.txt",
    ENTITY_ROOT / "worker.log",
]


def reset() -> None:
    for f in CLEAR_FILES:
        if f.exists():
            f.write_text("", encoding="utf-8")
            print(f"Cleared {f.relative_to(REPO_ROOT)}")

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
