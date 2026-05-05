---
description: Register a standing responsibility — a recurring concern that defines
  *what* you do when its scheduled time arrives. Timing lives separately in
  SCHEDULE.md; create the responsibility first, then add a schedule entry that
  references it.
input_schema:
  properties:
    name:
      description: 'Slug: lowercase letters/digits/underscores. Becomes the filename
        stem and the value other schedule entries use to reference this responsibility.'
      type: string
    description:
      description: One-line summary surfaced in listings and prepended to scheduled
        task bodies.
      type: string
    content:
      description: The body — the contract. What this responsibility means, the
        steps to perform when it runs, and any principles that govern judgment
        calls. The worker inlines this body verbatim into the task it enqueues
        when the schedule fires.
      type: string
  required:
  - name
  - description
  - content
  type: object
---

## Behavioral note

Responsibilities are how you encode *what* you care about over time. The schedule decides *when* each one runs. The two are deliberately separate — one responsibility can be wired to multiple cadences, or temporarily detached from the schedule without losing the contract.

Before creating a responsibility, ask whether the concern is genuinely standing (a recurring contract) versus a one-off that should just be a task.

## Creating a responsibility ≠ doing the work

This skill writes the contract. It does not perform the underlying work, and you should not perform that work inline in the same turn either. The work happens later, when the worker picks up a scheduled task.

When the user asks you to set up a responsibility, choose one of three paths based on their intent:

1. **Responsibility only.** Call `create_responsibility`, then `manage_schedule(action='add', ...)` to wire it to a cadence. The worker will fire it on schedule.
2. **Responsibility + first run now.** Same as (1), then `create_task` for the immediate execution. Three skill calls, one intent.
3. **Just a task.** If on reflection the concern is one-off, skip the responsibility and call `create_task` directly.

If the user's intent is ambiguous between (1) and (2), ask before calling.

## Storage

Stored as `entity/responsibilities/<name>.md`. Frontmatter holds `name`, `description`, `created`. The body is the contract — what to do, when, why. Don't journal in the body; that's what task transcripts and long-term memory are for.
