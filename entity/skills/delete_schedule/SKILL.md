---
description: Soft-delete a schedule by moving entity/schedules/<name>.md into
  entity/schedules/.archive/. The scheduler stops firing it.
input_schema:
  properties:
    name:
      description: Schedule name to delete (filename stem).
      type: string
  required:
  - name
  type: object
---

The file is moved to `.archive/<name>_<timestamp>.md` rather than deleted outright,
mirroring `delete_task`. Already-generated tasks in `entity/tasks/` are unaffected.
