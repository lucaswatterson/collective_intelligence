"""Reset the entity to a fresh (unborn) state.

Removes `entity/` entirely. On the next `uv run main.py`, the harness will
rebootstrap the workspace from `harness/template/`.
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.config import load_settings


def reset() -> None:
    settings = load_settings()
    if settings.entity_root.exists():
        shutil.rmtree(settings.entity_root)
        print(f"Removed {settings.entity_root.relative_to(settings.repo_root)}/")
    else:
        print(f"{settings.entity_root.relative_to(settings.repo_root)}/ already gone.")
    print("Run `uv run main.py` to rebootstrap.")


if __name__ == "__main__":
    reset()
