---
description: Soft-delete a skill by moving its folder to entity/skills/.archive/<name>_<timestamp>/. Recoverable. Refuses to delete delete_skill itself (would brick further deletions).
input_schema:
  type: object
  properties:
    name:
      type: string
      description: "Skill name to delete."
  required: [name]
---

# delete_skill

Moves `entity/skills/<name>/` to `entity/skills/.archive/<name>_<UTC-timestamp>/`. The skill disappears from the live tool list next turn. Recover by moving the folder back out of `.archive/`.

Refuses to delete `delete_skill` itself — losing this tool would be hard to recover from in-session.
