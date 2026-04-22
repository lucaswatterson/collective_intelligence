---
description: Modify an existing schedule in entity/schedules/. Can change interval,
  enabled flag, task title/priority/tags, or replace the body template.
input_schema:
  properties:
    name:
      description: Schedule name to update (filename stem).
      type: string
    interval:
      description: New interval string (e.g. '30m', '1h').
      type: string
    enabled:
      description: Enable or disable the schedule.
      type: boolean
    task_title:
      description: New title for generated tasks.
      type: string
    task_priority:
      description: Priority for generated tasks.
      enum:
      - low
      - medium
      - high
      type: string
    task_tags:
      description: Replace the tag list applied to generated tasks.
      items:
        type: string
      type: array
    content:
      description: Replace the body template (the task body).
      type: string
  required:
  - name
  type: object
---

Fields that are omitted are left unchanged. Interval is validated; an invalid
value is rejected. `last_run` is not modified by this skill.
