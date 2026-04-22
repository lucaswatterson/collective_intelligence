---
description: Read a long-term memory from entity/memory/long_term/ by filename or
  partial name match.
input_schema:
  properties:
    filename:
      description: Filename of the memory (e.g. '20260419_011011_lucas_prefers_concise_answers.md').
        Partial matches are supported if unambiguous.
      type: string
  required:
  - filename
  type: object
---

## Usage

- Pass the full filename or a partial string — if only one memory matches, it will be returned.
- If multiple match, you'll be asked to be more specific.
- Use `list_memories` first if you need to find the exact filename.
