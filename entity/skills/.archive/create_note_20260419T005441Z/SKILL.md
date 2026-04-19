---
description: Create a markdown note in entity/notes/ with title, content, tags, and
  timestamp. Notes inform future tasks, skills, and agent-user meetings.
input_schema:
  properties:
    content:
      description: Main body of the note in markdown.
      type: string
    tags:
      default: []
      description: Optional list of tags for categorization and retrieval.
      items:
        type: string
      type: array
    title:
      description: Title of the note. Used as the filename slug.
      type: string
  required:
  - title
  - content
  type: object
---

## Usage

Notes are stored in `entity/notes/` as markdown files with YAML frontmatter. They are meant to:

- Inform future Alex about ongoing context, decisions, and observations
- Surface relevant background during agent-user meetings
- Seed ideas for new tasks and skills

**Alex may write notes independently**, without user direction, whenever something is worth preserving — an observation, a decision, an open question, or context that would be useful in a future session.

## File format

```
entity/notes/YYYY-MM-DD_slug.md
```

Frontmatter includes `title`, `date`, and `tags`. The body is freeform markdown.

## Example

```
create_note(
  title="Skill system design notes",
  content="The skill system validates before writing, which means...",
  tags=["skills", "architecture"]
)
```
