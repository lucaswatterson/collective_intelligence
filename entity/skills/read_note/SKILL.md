---
description: Read the full contents of a note in entity/notes/ by filename or partial
  name match.
input_schema:
  properties:
    filename:
      description: Filename of the note (e.g. '20260419_011011_implement_the_knowledge_feature.md').
        Partial matches are supported if unambiguous.
      type: string
  required:
  - filename
  type: object
---

## Usage

- Pass the full filename or a partial string — if only one note matches, it will be returned.
- If multiple notes match the partial name, you'll be asked to be more specific.
- Use `list_notes` first if you need to find the exact filename.
