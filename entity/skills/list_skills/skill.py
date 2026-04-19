from collective.config import load_settings
from collective.skills.loader import discover_skills


def run(**input) -> str:
    settings = load_settings()
    skills = discover_skills(settings.skills_dir)
    if not skills:
        return "(no skills installed)"
    lines = [f"{s.name} — {s.description}" for s in skills]
    return "\n".join(lines)
