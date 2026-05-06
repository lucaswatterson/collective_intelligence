"""Install the Google Workspace skills into the entity directory.

Copies skill templates from `integrations/google/skills/` into
`entity/skills/`. The harness has no dependency on the templates — they exist
only to be copied here on demand. This is the opt-in entry point.

Pass --force to overwrite skills that are already installed (useful when the
templates change). Without --force, existing skills are left alone.
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.config import load_settings


SOURCE_DIR = REPO_ROOT / "integrations" / "google" / "skills"
GUARDS_SOURCE = REPO_ROOT / "integrations" / "google" / "guards.py"


def install(force: bool) -> int:
    settings = load_settings()
    dest_root = settings.skills_dir
    dest_root.mkdir(parents=True, exist_ok=True)

    if not SOURCE_DIR.exists():
        print(f"Error: source templates not found at {SOURCE_DIR}")
        return 1

    skill_sources = sorted(p for p in SOURCE_DIR.iterdir() if p.is_dir())
    if not skill_sources:
        print(f"Error: no skill templates under {SOURCE_DIR}")
        return 1

    installed: list[str] = []
    overwritten: list[str] = []
    skipped: list[str] = []

    for src in skill_sources:
        dst = dest_root / src.name
        if dst.exists():
            if not force:
                skipped.append(src.name)
                continue
            shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            overwritten.append(src.name)
        else:
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            installed.append(src.name)

    guards_dest_dir = settings.guards_dir
    guards_dest_dir.mkdir(parents=True, exist_ok=True)
    guards_dst = guards_dest_dir / "google.py"
    guards_status: str | None = None
    if not GUARDS_SOURCE.exists():
        print(f"Warning: guards plugin not found at {GUARDS_SOURCE}; skipping")
    elif guards_dst.exists():
        if force:
            shutil.copy2(GUARDS_SOURCE, guards_dst)
            guards_status = "overwritten"
        else:
            guards_status = "skipped"
    else:
        shutil.copy2(GUARDS_SOURCE, guards_dst)
        guards_status = "installed"

    for name in installed:
        print(f"Installed: entity/skills/{name}/")
    for name in overwritten:
        print(f"Overwrote: entity/skills/{name}/")
    for name in skipped:
        print(f"Skipped (already present): entity/skills/{name}/")
    if guards_status == "installed":
        print("Installed: entity/guards/google.py")
    elif guards_status == "overwritten":
        print("Overwrote: entity/guards/google.py")
    elif guards_status == "skipped":
        print("Skipped (already present): entity/guards/google.py")
    if skipped and not force:
        print("(re-run with --force to overwrite skipped skills)")

    print()
    gws_path = shutil.which("gws")
    if gws_path:
        print(f"gws found at {gws_path}.")
        print("If you haven't already, run: gws auth setup")
    else:
        print("gws not found on PATH.")
        print("Install with: brew install googleworkspace-cli")
        print("Then run:    gws auth setup")

    print()
    print("Restart the entity (or call `list_skills` from the TUI) to pick up the new skills.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite already-installed skills instead of skipping them.",
    )
    args = parser.parse_args()
    return install(force=args.force)


if __name__ == "__main__":
    sys.exit(main())
