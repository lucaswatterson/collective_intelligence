---
description: Register a recurring schedule that auto-materializes a task into
  entity/tasks/ on the given interval. Use for anything you want done on a cadence
  (e.g. generate a self image every hour).
input_schema:
  properties:
    name:
      description: Stable identifier for the schedule, slug-shaped (lowercase,
        alphanumeric/underscores). Used as the filename and as the `schedule` field
        on generated tasks. Must be unique.
      type: string
    interval:
      description: "Interval string: '<N>s', '<N>m', '<N>h', or '<N>d' (e.g. '30m',
        '1h', '2d')."
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
  - interval
  - task_title
  - content
  type: object
---

## Behavior

Creates `entity/schedules/<name>.md`. The worker checks schedules each poll; when
`last_run + interval <= now` (and no pending task already exists for this schedule),
it materializes a task in `entity/tasks/` with `schedule: <name>` in its frontmatter.

New schedules fire **immediately** on the next worker tick (last_run starts null),
then every interval thereafter. Fails if a schedule with the same name already exists.
