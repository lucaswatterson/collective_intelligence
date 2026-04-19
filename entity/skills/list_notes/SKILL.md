---
description: List all notes in entity/notes/, optionally filtered by tags. Returns
  title, filename, created date, tags, and author for each.
input_schema:
  properties:
    tags:
      description: Optional list of tags to filter by. Returns notes that match ANY
        of the supplied tags.
      items:
        type: string
      type: array
  type: object
---

## Usage

- Call with no arguments to list all notes.
- Pass `tags` to filter: e.g. `["task"]` returns only notes tagged `task`.
- Results are sorted by filename (chronological, since filenames are timestamp-prefixed).
