---
description: Register a recurring schedule that auto-materializes a task into
  entity/tasks/ on a cadence. Two modes — (1) interval-based ('every 24h',
  drifts based on last_run), or (2) wall-clock 'at' ('every day at 16:05' in a
  timezone). Provide exactly one of `interval` or `at`.
input_schema:
  properties:
    name:
      description: Stable identifier for the schedule, slug-shaped (lowercase,
        alphanumeric/underscores). Used as the filename and as the `schedule` field
        on generated tasks. Must be unique.
      type: string
    interval:
      description: "Interval string: '<N>s', '<N>m', '<N>h', or '<N>d' (e.g. '30m',
        '1h', '2d'). Mutually exclusive with `at`. Fires when last_run + interval
        <= now — drifts based on when it first fires."
      type: string
    at:
      description: "Wall-clock time of day in 24-hour 'HH:MM' (or 'HH:MM:SS') form,
        e.g. '16:05'. Fires once per day at that time. Mutually exclusive with
        `interval`. Resolved in the `timezone` field (defaults to the machine's
        local timezone)."
      type: string
    timezone:
      description: "IANA timezone name for `at`, e.g. 'America/Los_Angeles',
        'UTC', 'Europe/London'. Optional; defaults to the machine's local
        timezone. Ignored when using `interval`."
      type: string
    task_title:
      description: Title for each generated task.
      type: string
    content:
      description: Body template — becomes the body of each generated task verbatim.
      type: string
    task_priority:
      description: Priority for generated tasks. Defaults to 'medium'.
      enum:
      - low
      - medium
      - high
      type: string
    task_tags:
      description: Optional tags applied to every generated task.
      items:
        type: string
      type: array
    enabled:
      description: Whether the schedule is active. Defaults to true.
      type: boolean
    author:
      description: Author field on generated tasks. Defaults to 'agent'.
      type: string
  required:
  - name
  - task_title
  - content
  type: object
---

## Behavior

Creates `entity/schedules/<name>.md`. The worker checks schedules each poll;
when due (and no pending task already exists for this schedule), it
materializes a task in `entity/tasks/` with `schedule: <name>` in its
frontmatter.

**Interval mode** (`interval: 24h`): fires the first time on the next worker
tick (last_run starts null), then every interval thereafter. Drifts — "24h
after the last run," not a fixed wall-clock moment.

**At mode** (`at: "16:05"`, optional `timezone: "America/Los_Angeles"`):
fires once per day at that local wall-clock time. First run waits for the
next boundary — a schedule created at 9AM with `at: "16:05"` fires at
16:05 that same day, not immediately. DST transitions are handled
correctly.

Provide exactly one of `interval` or `at`. Fails if both or neither are
given, or if a schedule with the same name already exists.
