---
description: Update a long-term memory in entity/memory/long_term/ — refine content,
  change category/confidence/tags, or append more source sessions when a later session
  reinforces the same insight.
input_schema:
  properties:
    filename:
      description: Filename or partial name of the memory to update.
      type: string
    title:
      description: Optional new title.
      type: string
    replace_content:
      description: Fully replace the memory body with this content. Use when the insight
        has evolved enough that the old text is stale.
      type: string
    append_content:
      description: Append content to the memory body with a timestamp separator.
      type: string
    category:
      description: Change the category.
      enum:
      - user
      - self
      - collaboration
      - lesson
      - reference
      type: string
    confidence:
      description: Change the confidence level.
      enum:
      - low
      - medium
      - high
      type: string
    add_source_sessions:
      description: Additional session stems to merge into source_sessions (deduplicated).
      items:
        type: string
      type: array
    tags:
      description: Replace the tags list.
      items:
        type: string
      type: array
  required:
  - filename
  type: object
---

## Usage

- At least one mutating field (`title`, `replace_content`, `append_content`, `category`, `confidence`, `add_source_sessions`, `tags`) must be provided.
- `created` is preserved; `updated` is bumped to now.
- `add_source_sessions` merges (no duplicates); the frontmatter field stays a clean list.
- INDEX.md is regenerated after the update.
