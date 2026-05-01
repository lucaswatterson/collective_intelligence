---
description: Soft-delete a responsibility by moving it to entity/responsibilities/.archive/.
  Recoverable by moving the file back.
input_schema:
  properties:
    name:
      description: Name (filename stem) of the responsibility to archive.
      type: string
  required:
  - name
  type: object
---

Non-destructive — the file is moved to `.archive/<name>_<timestamp>.md`. Recover by moving it back to `entity/responsibilities/`. Prefer `update_responsibility` with `enabled: false` if you only want to pause it.
