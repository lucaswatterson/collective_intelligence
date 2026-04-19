---
description: Mark a task as done — sets status to 'done', stamps a completed timestamp,
  and moves it to entity/tasks/.completed/.
input_schema:
  properties:
    filename:
      description: Filename or partial name of the task to complete
      type: string
  required:
  - filename
  type: object
---

Non-destructive — completed tasks are preserved in `.completed/` for reference. Use `delete_task` if you want to archive (soft-delete) a task instead.
