from harness.config import load_settings
from harness.skills.meta import MetaSkillError, archive_skill


def run(**input) -> str:
    name = input.get("name")
    if not name:
        return "Error: missing required field 'name'."

    if name == "delete_skill":
        return (
            "Error: refusing to delete 'delete_skill' — without it you'd have no way "
            "to delete other skills in-session. Remove it manually from the filesystem "
            "if that's really what you want."
        )

    settings = load_settings()
    try:
        target = archive_skill(settings.skills_dir, name)
    except MetaSkillError as exc:
        return f"Error: {exc}"

    return f"Archived skill {name!r} to {target}. No longer available next turn."
