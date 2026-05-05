---
description: Update a responsibility — change its description or replace its body.
  Timing lives in SCHEDULE.md (see `manage_schedule`); this skill does not touch
  cadence.
input_schema:
  properties:
    name:
      description: Name (filename stem) of the responsibility to update.
      type: string
    description:
      description: New one-line description.
      type: string
    replace_content:
      description: Fully replace the body (the contract section). Use for genuine
        edits to what the responsibility means or how it should be handled.
      type: string
  required:
  - name
  type: object
---

The body is the contract — what gets inlined into a task whenever the schedule fires for this responsibility. Edit it when the actual procedure or principles change. Don't journal in it; logging belongs in task transcripts and long-term memory.

To change *when* this responsibility runs, use `manage_schedule` (action='update') — the schedule entry owns timing.
