---
description: Partially update an existing skill. Supply only the fields you want to change (description, input_schema, body, or skill_py). Omitted fields are preserved. The updated skill is validated before being written.
input_schema:
  type: object
  properties:
    name:
      type: string
      description: "Skill name to update."
    description:
      type: string
      description: "New one-line description. Omit to keep the existing one."
    input_schema:
      type: object
      description: "New JSON Schema for inputs. Omit to keep the existing one."
    body:
      type: string
      description: "New markdown body. Omit to keep existing. Pass empty string to clear."
    skill_py:
      type: string
      description: "New full skill.py source. Omit to keep existing."
  required: [name]
---

# update_skill

Merges the fields you pass with the skill's current state, then revalidates and writes. If validation fails, the on-disk skill is unchanged.

Call `read_skill` first if you need to see current state before patching.
