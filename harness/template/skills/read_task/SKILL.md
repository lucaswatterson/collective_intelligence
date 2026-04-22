---
description: Read the full contents of a task in entity/tasks/ by filename or partial
  name match.
input_schema:
  properties:
    filename:
      description: Filename or partial name of the task to read
      type: string
  required:
  - filename
  type: object
---

Supports partial filename matching. If multiple tasks match, returns an error listing the matches — be more specific. Use `list_tasks` first if you need to find the exact filename.
