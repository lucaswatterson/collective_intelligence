import os

def run(path: str, content: str, overwrite: bool = False, **kwargs) -> str:
    # Resolve entity root: two levels up from this file (entity/skills/write_file/skill.py)
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    entity_dir = os.path.dirname(os.path.dirname(skill_dir))

    # Sanitize path — no escaping entity dir
    clean_path = os.path.normpath(path.lstrip("/"))
    if clean_path.startswith(".."):
        return f"Error: path '{path}' escapes the entity directory."

    full_path = os.path.join(entity_dir, clean_path)

    if os.path.exists(full_path) and not overwrite:
        return f"Error: file already exists at '{full_path}'. Pass overwrite=true to replace it."

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Written {len(content)} characters to {full_path}"
