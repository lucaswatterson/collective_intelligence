from typing import Any

from collective.skills.loader import Skill


def to_anthropic_tools(skills: list[Skill]) -> list[dict[str, Any]]:
    tools = []
    for skill in skills:
        description = skill.description
        if skill.body:
            description = f"{description}\n\n{skill.body}".strip()
        tools.append(
            {
                "name": skill.name,
                "description": description,
                "input_schema": skill.input_schema,
            }
        )
    return tools


def execute(skills: list[Skill], name: str, tool_input: dict[str, Any]) -> str:
    skill = next((s for s in skills if s.name == name), None)
    if skill is None:
        return f"Error: skill '{name}' not found."
    try:
        result = skill.run(**tool_input)
    except Exception as exc:  # surface the failure back to the model
        return f"Error executing skill '{name}': {exc}"
    return str(result) if result is not None else "(no output)"
