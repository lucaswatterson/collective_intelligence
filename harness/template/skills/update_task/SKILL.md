---
description: Update a task in entity/tasks/ — change status, priority, due, tags,
  title, or append/replace content body.
input_schema:
  properties:
    append_content:
      description: Content to append to the task body (timestamped)
      type: string
    due:
      description: New due date (ISO format)
      type: string
    filename:
      description: Filename or partial name of the task to update
      type: string
    priority:
      description: New priority
      enum:
      - low
      - medium
      - high
      type: string
    replace_content:
      description: Fully replace the task body. Use with care.
      type: string
    status:
      description: New status
      enum:
      - todo
      - in-progress
      - blocked
      type: string
    tags:
      description: Replace tags with this list
      items:
        type: string
      type: array
    title:
      description: New title
      type: string
  required:
  - filename
  type: object
---

At least one of the optional fields must be provided to do anything useful. `append_content` is preferred over `replace_content` for incremental updates — it adds a timestamped section. Use `complete_task` to mark a task done and move it to `.completed/`.
