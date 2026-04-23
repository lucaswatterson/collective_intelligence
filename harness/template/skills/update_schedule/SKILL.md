---
description: Modify an existing schedule in entity/schedules/. Can change
  interval, at-time, timezone, enabled flag, task title/priority/tags, or
  replace the body template. Switching between interval-mode and at-mode
  clears the opposite field.
input_schema:
  properties:
    name:
      description: Schedule name to update (filename stem).
      type: string
    interval:
      description: "New interval string (e.g. '30m', '1h'). Setting this clears
        any existing `at` and `timezone` (switches the schedule to interval mode)."
      type: string
    at:
      description: "New wall-clock time of day in 'HH:MM' 24-hour form, e.g.
        '16:05'. Setting this clears any existing `interval` (switches to at
        mode). Combine with `timezone` to anchor to a specific zone."
      type: string
    timezone:
      description: "IANA timezone name for `at`, e.g. 'America/Los_Angeles'.
        Only meaningful in at-mode. Pass an empty string to clear and fall
        back to system local tz."
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

Fields that are omitted are left unchanged. `interval` and `at` are
validated; invalid values are rejected. Setting one of them clears the
other (plus `timezone` when switching off at-mode) so the scheduler always
sees exactly one mode. `last_run` is not modified by this skill.
