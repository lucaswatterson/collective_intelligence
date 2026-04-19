import json

from collective.config import load_settings
from collective.skills.meta import MetaSkillError, read_skill_files


def run(**input) -> str:
    name = input.get("name")
    if not name:
        return "Error: missing required field 'name'."

    settings = load_settings()
    try:
        data = read_skill_files(settings.skills_dir, name)
    except MetaSkillError as exc:
        return f"Error: {exc}"

    return (
        f"name: {data['name']}\n"
        f"description: {data['description']}\n"
        f"input_schema: {json.dumps(data['input_schema'], indent=2)}\n\n"
        f"--- body (SKILL.md) ---\n{data['body']}\n\n"
        f"--- skill.py ---\n{data['skill_py']}"
    )
