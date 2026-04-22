---
description: Create a new skill in entity/skills/ by writing its SKILL.md and skill.py. The skill is validated (frontmatter parses, skill.py imports, run() is callable) before being written. Takes effect in the current session.
input_schema:
  type: object
  properties:
    name:
      type: string
      description: "Skill name. Must match ^[a-z][a-z0-9_]*$ and be unique within entity/skills/."
    description:
      type: string
      description: "One-line description shown to you as the tool description. Make it specific so future-you picks the right tool."
    input_schema:
      type: object
      description: "JSON Schema describing the skill's inputs. Must be {\"type\": \"object\", \"properties\": {...}, ...}."
    body:
      type: string
      description: "Markdown body of SKILL.md appended to the description. Use it for usage notes, invariants, examples. Empty string if none."
    skill_py:
      type: string
      description: "Full Python source for skill.py. Must define a callable run(**input) that returns a string (or None)."
  required: [name, description, input_schema, body, skill_py]
---

# create_skill

Creates a new skill at `entity/skills/<name>/`. Fails loudly if validation fails and writes nothing.

## Contract

- `name` is unique, lowercase snake_case.
- `skill.py` must import cleanly and expose a callable `run(**input)`.
- `input_schema` must be a valid JSON Schema object.
- On success, the new skill is available as a tool in the next turn of this session.

## Example — a trivial echo skill

```
create_skill(
  name="echo",
  description="Return the text argument verbatim. Useful for testing.",
  input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
  body="",
  skill_py="def run(**input):\n    return input['text']\n",
)
```

If `name` already exists, use `update_skill` instead.
