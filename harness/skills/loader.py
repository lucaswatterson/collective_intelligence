import importlib.util
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter


@dataclass
class Skill:
    name: str
    description: str
    input_schema: dict[str, Any]
    body: str
    run: Callable[..., str]
    path: Path


def discover_skills(skills_dir: Path) -> list[Skill]:
    if not skills_dir.exists():
        return []
    skills: list[Skill] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        if skill_md.parent.name.startswith("."):
            continue
        skills.append(load_skill(skill_md))
    return skills


def load_skill(skill_md: Path) -> Skill:
    parsed = frontmatter.load(skill_md)
    meta = parsed.metadata
    name = meta.get("name") or skill_md.parent.name
    description = meta.get("description") or ""
    input_schema = meta.get("input_schema") or {"type": "object", "properties": {}}

    skill_py = skill_md.parent / "skill.py"
    if not skill_py.exists():
        raise FileNotFoundError(
            f"Skill '{name}' is missing skill.py at {skill_py}"
        )

    module_name = f"_harness_skill_{name}"
    spec = importlib.util.spec_from_file_location(module_name, skill_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load skill module for {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    run = getattr(module, "run", None)
    if not callable(run):
        raise AttributeError(f"Skill '{name}' module must define run(**input)")

    return Skill(
        name=name,
        description=description,
        input_schema=input_schema,
        body=parsed.content.strip(),
        run=run,
        path=skill_md.parent,
    )
