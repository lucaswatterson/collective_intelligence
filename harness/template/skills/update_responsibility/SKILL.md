---
description: Update a responsibility — change description, enabled, review_interval,
  or replace its body. Any call automatically bumps `last_reviewed` to now (so a
  no-op call with just `name` works as "I reviewed this and decided nothing was
  needed").
input_schema:
  properties:
    name:
      description: Name (filename stem) of the responsibility to update.
      type: string
    description:
      description: New one-line description.
      type: string
    enabled:
      description: Toggle whether this responsibility surfaces in planning ticks.
      type: boolean
    review_interval:
      description: How often this responsibility wants attention. Human-friendly
        string like '30m', '4h', '1d', '1w'. Pass null to clear (review on every
        tick).
      type: string
    last_reviewed:
      description: ISO timestamp marking when you most recently reviewed this.
        Normally you don't pass this — it auto-bumps to now on every call. Pass
        an explicit value only to backdate or override.
      type: string
    replace_content:
      description: Fully replace the body (the contract section). Use for genuine
        edits to what the responsibility means or how it should be handled.
      type: string
  required:
  - name
  type: object
---

Calling `update_responsibility(name=...)` with no other arguments is a valid "mark as reviewed" — it bumps `last_reviewed` to now so the responsibility doesn't resurface until its `review_interval` elapses again.

There is no `append_content` / journal mode. Logging belongs in task transcripts and long-term memory, not inside the responsibility file. The body is the contract; keep it stable.
