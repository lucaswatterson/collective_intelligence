"""Materialize the entity workspace from the harness-side template.

`entity/` is runtime state, gitignored. On first boot it does not exist; this
module copies `harness/template/` into `settings.entity_root` so the rest of
the harness can assume the filesystem layout is in place.
"""

import shutil

from harness.config import Settings


def bootstrap_entity(settings: Settings) -> None:
    """Copy the template tree into entity_root if it doesn't already exist.

    Idempotent: if entity_root exists, does nothing. We do not merge or
    overwrite — the template is the seed, not an authority.
    """
    if settings.entity_root.exists():
        return

    shutil.copytree(settings.template_dir, settings.entity_root)

    for gitkeep in settings.entity_root.rglob(".gitkeep"):
        gitkeep.unlink()
