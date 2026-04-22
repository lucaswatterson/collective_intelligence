from harness.config import load_settings
from harness.skills.meta import (
    MetaSkillError,
    commit_staged_skill,
    stage_and_validate,
    validate_name,
)


def run(**input) -> str:
    try:
        name = input["name"]
        description = input["description"]
        input_schema = input["input_schema"]
        body = input.get("body", "")
        skill_py = input["skill_py"]
    except KeyError as exc:
        return f"Error: missing required field {exc.args[0]!r}."

    settings = load_settings()
    skills_dir = settings.skills_dir

    try:
        validate_name(name)
    except MetaSkillError as exc:
        return f"Error: {exc}"

    if (skills_dir / name).exists():
        return (
            f"Error: skill {name!r} already exists. Use update_skill to modify it, "
            "or delete_skill first if you want to recreate from scratch."
        )

    try:
        staging = stage_and_validate(name, description, input_schema, body, skill_py)
    except MetaSkillError as exc:
        return f"Error: {exc}"

    target = commit_staged_skill(staging, skills_dir, name)
    return f"Created skill {name!r} at {target}. It is live for the next turn."
