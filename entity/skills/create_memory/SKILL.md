---
description: Create a long-term memory in entity/memory/long_term/ — a durable,
  distilled fact or lesson meant to persist across sessions. Use during reflection
  to promote short-term insights into memory that survives.
input_schema:
  properties:
    title:
      description: Short human-readable title for the memory.
      type: string
    content:
      description: The memory body in markdown. Lead with a one-line gist — it becomes
        the INDEX.md summary.
      type: string
    category:
      description: One of user, self, collaboration, lesson, reference.
      enum:
      - user
      - self
      - collaboration
      - lesson
      - reference
      type: string
    confidence:
      description: How confident you are in this memory. One of low, medium, high.
        Defaults to medium.
      enum:
      - low
      - medium
      - high
      type: string
    source_sessions:
      description: Session stems this memory was distilled from (e.g. '2026-04-19T14-22-01').
      items:
        type: string
      type: array
    tags:
      description: Optional free-form tags for cross-cutting grouping.
      items:
        type: string
      type: array
  required:
  - title
  - content
  - category
  type: object
---

## Usage

Long-term memories live in `entity/memory/long_term/` as markdown files with YAML frontmatter. Filenames are timestamp + slugified title.

### Categories
- `user` — facts/preferences about Lucas
- `self` — things about me that aren't load-bearing enough for IDENTITY.md
- `collaboration` — how we work together
- `lesson` — generalized takeaway from a specific incident
- `reference` — durable technical/domain facts

### When to use
- During a `consolidate_memory` reflection: for each distilled insight, create a memory.
- Prefer `update_memory` if an existing memory covers the same ground — check INDEX.md first.

### Notes
- INDEX.md is automatically regenerated after every create/update/delete.
- The first line of `content` becomes the INDEX gist, so lead with a summary.
