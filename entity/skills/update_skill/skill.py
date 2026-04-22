from harness.config import load_settings
from harness.skills.meta import (
    MetaSkillError,
    commit_staged_skill,
    read_skill_files,
    stage_and_validate,
)


_SENTINEL = object()


def run(**input) -> str:
    name = input.get("name")
    if not name:
        return "Error: missing required field 'name'."

    settings = load_settings()
    skills_dir = settings.skills_dir

    try:
        current = read_skill_files(skills_dir, name)
    except MetaSkillError as exc:
        return f"Error: {exc}"

    merged = {
        "description": input.get("description", _SENTINEL),
        "input_schema": input.get("input_schema", _SENTINEL),
        "body": input.get("body", _SENTINEL),
        "skill_py": input.get("skill_py", _SENTINEL),
    }
    for key, value in merged.items():
        if value is _SENTINEL:
            merged[key] = current[key]

    changed = [k for k, v in input.items() if k != "name" and v is not None]
    if not changed:
        return f"Error: no fields to update for {name!r}. Pass at least one of description, input_schema, body, skill_py."

    try:
        staging = stage_and_validate(
            name,
            merged["description"],
            merged["input_schema"],
            merged["body"],
            merged["skill_py"],
        )
    except MetaSkillError as exc:
        return f"Error: {exc}"

    commit_staged_skill(staging, skills_dir, name)
    return f"Updated skill {name!r} (fields: {', '.join(sorted(changed))}). Live next turn."
