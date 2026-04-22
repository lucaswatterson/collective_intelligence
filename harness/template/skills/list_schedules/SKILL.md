---
description: List all recurring schedules in entity/schedules/ with interval,
  enabled state, last_run, and next_fire.
input_schema:
  properties: {}
  type: object
---

Returns one line per schedule showing `name`, `interval`, `enabled`, `last_run`,
and computed `next_fire`. Disabled and malformed schedules are included with a note.
