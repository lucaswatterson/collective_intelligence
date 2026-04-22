---
description: Create a task in entity/tasks/ with frontmatter. Ask clarifying questions
  before calling — tasks should be well-thought-out plans for future action.
input_schema:
  properties:
    author:
      description: '''agent'' or ''user''. Defaults to ''user''.'
      type: string
    content:
      description: The body of the task — a detailed plan for action
      type: string
    due:
      description: Optional due date (ISO format, e.g. 2026-05-01)
      type: string
    priority:
      description: Task priority. Defaults to 'medium'.
      enum:
      - low
      - medium
      - high
      type: string
    status:
      description: Initial status. Defaults to 'todo'.
      enum:
      - todo
      - in-progress
      - blocked
      type: string
    tags:
      description: Optional tags
      items:
        type: string
      type: array
    title:
      description: Human-readable task title
      type: string
  required:
  - title
  - content
  type: object
---

## Behavioral note

Before calling this skill, ask enough clarifying questions to produce a well-scoped task with a meaningful plan in the body. A task is not a one-liner — it should capture intent, scope, expected outcome, and any known blockers or dependencies.

## Fields

- `title` — short, actionable name
- `content` — the plan: what, why, how, and any relevant context
- `status` — `todo` (default), `in-progress`, `blocked`
- `priority` — `low`, `medium` (default), `high`
- `due` — optional ISO date string
- `tags` — optional list
- `author` — `agent` or `user`

## Storage

Tasks live in `entity/tasks/` as `<timestamp>_<slug>.md`. Completed tasks move to `.completed/`. Deleted tasks move to `.archive/`.
