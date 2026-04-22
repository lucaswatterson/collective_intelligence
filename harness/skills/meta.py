import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import frontmatter

from harness.skills.loader import load_skill


META_SKILL_NAMES: frozenset[str] = frozenset(
    {"create_skill", "read_skill", "update_skill", "delete_skill", "list_skills"}
)

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class MetaSkillError(Exception):
    """Raised for user-visible validation failures in meta-skills."""


def validate_name(name: str) -> None:
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise MetaSkillError(
            f"Invalid skill name {name!r}: must match ^[a-z][a-z0-9_]*$"
        )


def validate_input_schema(input_schema: Any) -> None:
    if not isinstance(input_schema, dict):
        raise MetaSkillError("input_schema must be a JSON object (dict).")
    if input_schema.get("type") != "object":
        raise MetaSkillError("input_schema must have \"type\": \"object\".")
    properties = input_schema.get("properties", {})
    if not isinstance(properties, dict):
        raise MetaSkillError("input_schema.properties must be an object.")


def render_skill_md(description: str, input_schema: dict[str, Any], body: str) -> str:
    post = frontmatter.Post(
        body,
        description=description,
        input_schema=input_schema,
    )
    return frontmatter.dumps(post) + "\n"


def stage_and_validate(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    body: str,
    skill_py: str,
) -> Path:
    """Write the skill to a tempdir and load it to verify it's importable.

    Returns the staging directory. Caller is responsible for moving it
    into place or cleaning up.
    """
    validate_name(name)
    if not isinstance(description, str) or not description.strip():
        raise MetaSkillError("description must be a non-empty string.")
    validate_input_schema(input_schema)
    if not isinstance(body, str):
        raise MetaSkillError("body must be a string (use \"\" for empty).")
    if not isinstance(skill_py, str) or not skill_py.strip():
        raise MetaSkillError("skill_py must be a non-empty Python source string.")

    staging_root = Path(tempfile.mkdtemp(prefix=f"skill_stage_{name}_"))
    staging = staging_root / name
    staging.mkdir()
    (staging / "SKILL.md").write_text(
        render_skill_md(description, input_schema, body), encoding="utf-8"
    )
    (staging / "skill.py").write_text(skill_py, encoding="utf-8")

    try:
        load_skill(staging / "SKILL.md")
    except Exception as exc:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise MetaSkillError(f"Skill failed to load: {exc}") from exc

    return staging


def commit_staged_skill(staging: Path, skills_dir: Path, name: str) -> Path:
    """Move a staged skill dir into skills_dir/<name>/. Removes prior if present."""
    skills_dir.mkdir(parents=True, exist_ok=True)
    target = skills_dir / name
    if target.exists():
        shutil.rmtree(target)
    shutil.move(str(staging), str(target))
    # staging's parent tempdir is now empty; clean it up
    try:
        staging.parent.rmdir()
    except OSError:
        pass
    return target


def read_skill_files(skills_dir: Path, name: str) -> dict[str, Any]:
    validate_name(name)
    skill_dir = skills_dir / name
    skill_md = skill_dir / "SKILL.md"
    skill_py = skill_dir / "skill.py"
    if not skill_md.exists() or not skill_py.exists():
        raise MetaSkillError(f"Skill {name!r} not found at {skill_dir}.")
    parsed = frontmatter.load(skill_md)
    return {
        "name": parsed.metadata.get("name") or name,
        "description": parsed.metadata.get("description") or "",
        "input_schema": parsed.metadata.get("input_schema")
        or {"type": "object", "properties": {}},
        "body": parsed.content,
        "skill_py": skill_py.read_text(encoding="utf-8"),
    }


def archive_skill(skills_dir: Path, name: str) -> Path:
    validate_name(name)
    source = skills_dir / name
    if not source.exists():
        raise MetaSkillError(f"Skill {name!r} not found.")
    archive_root = skills_dir / ".archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = archive_root / f"{name}_{stamp}"
    shutil.move(str(source), str(target))
    return target
