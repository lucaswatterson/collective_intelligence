---
description: Return the full source of an existing skill — its SKILL.md frontmatter, body, and skill.py. Use before update_skill to see what's there.
input_schema:
  type: object
  properties:
    name:
      type: string
      description: "Skill name to read."
  required: [name]
---

# read_skill

Returns a structured dump of the skill's files so you can decide what to change. Pair with `update_skill` for partial edits.
