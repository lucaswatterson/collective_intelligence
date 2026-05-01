---
description: Register a standing responsibility — a recurring concern reviewed during
  planning ticks (when the task queue goes empty). You set a `review_interval`
  per responsibility; the worker only surfaces it when that interval has elapsed
  since `last_reviewed`.
input_schema:
  properties:
    name:
      description: 'Slug: lowercase letters/digits/underscores. Becomes the filename
        stem.'
      type: string
    description:
      description: One-line summary surfaced in the planning prompt and listings.
      type: string
    content:
      description: The body — the contract. What this responsibility means, when it
        matters, what staying on top of it looks like.
      type: string
    enabled:
      description: Whether the planning prompt surfaces this responsibility. Default
        true.
      type: boolean
    review_interval:
      description: How often this responsibility wants attention. Human-friendly
        string like '30m', '4h', '1d', '1w'. Omit for "every planning tick".
      type: string
  required:
  - name
  - description
  - content
  type: object
---

## Behavioral note

Responsibilities are how you encode what you care about over time. Before creating one, ask whether the concern is genuinely standing — something you'll want to revisit across planning ticks — versus a one-off that should just be a task.

Pick `review_interval` for the cadence the underlying concern actually needs — email might want `30m`, a daily review wants `1d`, a long-running watch might want `1w`. Tighter intervals mean more frequent prompts; only commit to one if you'd genuinely act on the prompt that often.

## Creating a responsibility ≠ doing the work

This skill writes the contract. It does not perform the underlying work, and you should not perform that work inline in the same turn either. Work happens through tasks the worker picks up — that's how it gets its own transcript and flows through the normal execution path. Doing it inline in chat collapses two different things into one and skips the worker entirely.

When the user asks you to set up a responsibility, choose one of three paths based on their intent:

1. **Responsibility only.** They want the cadence on the books; no immediate action. Call `create_responsibility` and stop. The worker will surface it on the next planning tick once its `review_interval` elapses.
2. **Responsibility + first run now.** They want both the cadence registered *and* the work done now. Call `create_responsibility`, then call `create_task` with a concrete plan for the first execution. Two skill calls, one intent. Do not invoke the underlying skill inline.
3. **Just a task.** If on reflection the concern is really one-off, skip `create_responsibility` and call `create_task` directly.

If the user's intent is ambiguous between (1) and (2), ask before calling.

## Storage

Stored as `entity/responsibilities/<name>.md`. Frontmatter holds metadata (`name`, `description`, `enabled`, `review_interval`, `created`, `last_reviewed`); the body is the contract — what to do, when, why. Don't journal in the body; that's what task transcripts and long-term memory are for.
