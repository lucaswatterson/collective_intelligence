---
description: Create a markdown note in entity/notes/ with frontmatter. Used by agent
  or user to store information, flag tasks, prep for meetings, or leave context for
  future sessions.
input_schema:
  properties:
    author:
      description: Who wrote the note. Use 'agent' or 'user'. Defaults to 'agent'.
      type: string
    content:
      description: The body of the note in plain text or markdown.
      type: string
    tags:
      description: Optional tags for categorization, e.g. ['task', 'meeting', 'idea',
        'memory'].
      items:
        type: string
      type: array
    title:
      description: The title of the note.
      type: string
  required:
  - title
  - content
  type: object
---

## Usage

Notes live in `entity/notes/` as markdown files with YAML frontmatter. Filenames are auto-generated from the timestamp and slugified title, making them sortable and human-readable.

### Frontmatter fields
- `title` — human-readable title
- `created` — UTC ISO timestamp
- `tags` — list of strings for loose categorization
- `author` — `agent` or `user`

### Tag conventions (soft)
- `task` — something that should be acted on
- `meeting` — prep or summary for a user/agent session
- `idea` — early-stage thought
- `memory` — context to carry forward
- `skill` — related to skill development

## Notes
- The `entity/notes/` directory is created automatically if it doesn't exist.
- Notes are append-only by design — edit via a future `update_note` skill.
