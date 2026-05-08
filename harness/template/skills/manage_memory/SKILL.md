---
description: Manage long-term memories in entity/memory/long_term/. Single dispatcher
  with action=create|update|delete|read|list. Mutating actions rebuild INDEX.md.
input_schema:
  type: object
  properties:
    action:
      description: What to do.
      enum:
      - create
      - update
      - delete
      - read
      - list
      - unconsolidated
      type: string
    title:
      description: (create) Short human-readable title. (update) Optional new title.
      type: string
    content:
      description: (create) The memory body in markdown. Lead with a one-line gist —
        it becomes the INDEX.md summary.
      type: string
    category:
      description: (create) Required category. (update) New category. (list) Optional
        filter.
      enum:
      - user
      - self
      - collaboration
      - lesson
      - reference
      type: string
    confidence:
      description: (create) How confident you are in this memory. Defaults to medium.
        (update) New confidence level.
      enum:
      - low
      - medium
      - high
      type: string
    source_sessions:
      description: (create) Session stems this memory was distilled from.
      items:
        type: string
      type: array
    tags:
      description: (create) Optional tags. (update) Replace the tags list. (list) Match
        any supplied tag.
      items:
        type: string
      type: array
    filename:
      description: (update / delete / read) Filename or partial name of the memory.
        Partial matches are supported if unambiguous.
      type: string
    replace_content:
      description: (update) Fully replace the memory body with this content.
      type: string
    append_content:
      description: (update) Append content with a timestamp separator.
      type: string
    add_source_sessions:
      description: (update) Additional session stems to merge into source_sessions
        (deduplicated).
      items:
        type: string
      type: array
  required:
  - action
---

## Usage

One skill, one dispatcher. Pick `action` and pass the fields it needs. INDEX.md is regenerated automatically after every mutating action.

### `action: create`
Create a new memory file at `entity/memory/long_term/<timestamp>_<slug>.md` with YAML frontmatter (`title`, `category`, `confidence`, `source_sessions`, `tags`, `created`, `updated`) and your markdown body.

- Required: `title`, `content`, `category`.
- Optional: `confidence` (default `medium`), `source_sessions`, `tags`.
- Lead `content` with a one-line gist — it becomes the INDEX summary.

### `action: update`
Refine an existing memory's body, change category/confidence/tags, or merge in additional source sessions.

- Required: `filename` (full or partial; ambiguous matches error).
- At least one mutating field must be supplied: `title`, `replace_content`, `append_content`, `category`, `confidence`, `add_source_sessions`, `tags`.
- `created` is preserved; `updated` is bumped to now.
- `add_source_sessions` deduplicates against the existing list.

### `action: delete`
Soft-delete by moving the memory to `entity/memory/long_term/.archive/<stem>_<timestamp>.md`. Recover by moving it back.

- Required: `filename`.

### `action: read`
Return the full text of one memory.

- Required: `filename`. Partial matches supported if unambiguous.

### `action: list`
- No filters → returns INDEX.md verbatim (cheap, pre-rendered).
- With `category` and/or `tags` → returns a filtered listing with title, filename, category, confidence, tags.

### `action: unconsolidated`
Return one short-term session stem per line — the sessions whose stems aren't yet in any long-term memory's `source_sessions`. Used by the `memory_consolidation` responsibility to pick the next batch to reflect on. Returns `"No unconsolidated sessions."` when caught up.

### Categories
- `user` — facts/preferences about Lucas
- `self` — things about me that aren't load-bearing enough for IDENTITY.md
- `collaboration` — how we work together
- `lesson` — generalized takeaway from a specific incident
- `reference` — durable technical/domain facts
