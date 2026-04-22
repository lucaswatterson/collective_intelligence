---
description: Write content to a file at any path within the entity directory. Creates
  parent directories as needed. Use for saving work artifacts, reports, and outputs.
input_schema:
  properties:
    content:
      description: Content to write to the file
      type: string
    overwrite:
      default: false
      description: If true, overwrite existing file. Defaults to false.
      type: boolean
    path:
      description: File path relative to the entity root (e.g. 'work/my-task/report.md')
      type: string
  required:
  - path
  - content
  type: object
---

## Usage

Write any content to a file within the entity directory. Parent directories are created automatically.

- `path` is relative to the `entity/` root
- Set `overwrite: true` to replace an existing file
- Returns the absolute path written on success

## Notes
- Does not escape the entity directory (paths are sandboxed)
- Use for saving work outputs, reports, research notes, and other artifacts
