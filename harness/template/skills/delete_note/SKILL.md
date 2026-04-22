---
description: Soft-delete a note by moving it to entity/notes/.archive/. Recoverable
  by moving the file back.
input_schema:
  properties:
    filename:
      description: Filename or partial name of the note to archive.
      type: string
  required:
  - filename
  type: object
---

## Usage

- Moves the note to `entity/notes/.archive/<original_stem>_<timestamp>.md`.
- Non-destructive — recover by moving the file back to `entity/notes/`.
- Partial filename matching is supported; will fail if the match is ambiguous.
