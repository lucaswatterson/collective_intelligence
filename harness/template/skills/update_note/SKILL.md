---
description: Update an existing note in entity/notes/ — append content, replace content,
  or update frontmatter fields (tags, title).
input_schema:
  properties:
    append_content:
      description: Content to append to the note body. A timestamp separator is added
        automatically.
      type: string
    filename:
      description: Filename or partial name of the note to update.
      type: string
    replace_content:
      description: Fully replace the note body with this content. Use with care.
      type: string
    tags:
      description: Replace the note's tags with this list.
      items:
        type: string
      type: array
    title:
      description: Update the note's title in frontmatter.
      type: string
  required:
  - filename
  type: object
---

## Usage

- At least one of `append_content`, `replace_content`, `tags`, or `title` must be meaningful to do anything.
- `append_content` adds a timestamped section at the end — preferred for incremental updates.
- `replace_content` overwrites the body — use only when a clean rewrite is intentional.
- `tags` and `title` update frontmatter only, leaving the body untouched (unless combined with content args).
