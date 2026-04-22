---
description: Soft-delete a task by moving it to entity/tasks/.archive/. Recoverable
  by moving the file back.
input_schema:
  properties:
    filename:
      description: Filename or partial name of the task to archive
      type: string
  required:
  - filename
  type: object
---

Non-destructive — the task is moved to `.archive/<original_stem>_<timestamp>.md`. Recover by moving it back to `entity/tasks/`. Partial filename matching is supported; will fail if ambiguous.
