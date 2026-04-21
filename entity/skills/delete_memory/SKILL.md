---
description: Soft-delete a long-term memory by moving it to entity/memory/long_term/.archive/.
  Recoverable by moving the file back.
input_schema:
  properties:
    filename:
      description: Filename or partial name of the memory to archive.
      type: string
  required:
  - filename
  type: object
---

## Usage

- Moves the memory to `entity/memory/long_term/.archive/<stem>_<timestamp>.md`.
- Non-destructive — recover by moving the file back.
- Partial filename matching is supported; will fail if the match is ambiguous.
- INDEX.md is regenerated after the move.
