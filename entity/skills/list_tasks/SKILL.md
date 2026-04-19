---
description: List tasks in entity/tasks/, optionally filtered by status, priority,
  or tags. Returns title, status, priority, due date, tags, and filename for each.
input_schema:
  properties:
    priority:
      description: Filter by priority
      enum:
      - low
      - medium
      - high
      type: string
    status:
      description: Filter by status
      enum:
      - todo
      - in-progress
      - blocked
      - done
      type: string
    tags:
      description: Filter by tags — returns tasks matching ANY supplied tag
      items:
        type: string
      type: array
  type: object
---

Returns active tasks only (not completed or archived). Use filters to narrow results. Results are sorted by filename (chronological).
