---
name: memory_consolidation
description: Reflect on recent sessions and distill only durable, decision-changing
  insights into long-term memory.
enabled: true
review_interval: 12h
created: '2026-05-01T21:59:31.393259+00:00'
last_reviewed: null
---

## Contract

1. Call `consolidate_memory` with `limit: 30` to pull the current INDEX, IDENTITY, and the oldest unconsolidated sessions.
2. For each session, decide whether anything durable came out of it. **The default answer is no.** Most sessions — especially short task sessions like chat/inbox checks — yield zero new memories.
3. For any insight that *does* clear the bar in Principles below: call `create_memory`, or `update_memory` if INDEX shows it's already covered (pass `add_source_sessions` so the reinforcement is recorded). Lead the body with a one-line gist; INDEX uses it.
4. Call `archive_session` on **every** session processed, including ones that produced no memory. A consolidated-but-unarchived session lingers in `short_term/` forever — `consolidate_memory` won't re-show it (its stem is already in some memory's `source_sessions`), but the file stays there.
5. If `consolidate_memory` reported more unconsolidated sessions than the limit, stop after this batch — the next tick picks up the rest. Don't try to drain the queue in one pass.
6. Call `complete_task`.

## Principles

The bar: a memory is worth keeping only if it answers **yes** to *"Will I make a different decision in a future session because this is in long-term memory?"* If the answer is no, maybe, or "it's nice context," archive without writing.

Tests to apply *before* calling `create_memory`:

- **Durability.** Will this still be true and relevant in a month? One-off task details, transient state, "today the user asked X" — no.
- **Derivability.** Can I get this from `IDENTITY.md`, the codebase, or `git log`? If yes, don't duplicate it into memory.
- **Generality.** Is this a pattern I've seen *more than once*, or a stance the user explicitly stated as durable? A single occurrence is rarely enough — prefer `update_memory` on the second occurrence to lift confidence over `create_memory` on the first.
- **Anti-noise.** "We worked on X today" / "fixed bug Y" / "reviewed PR Z" → no. The session transcript already records that. Memory is for what the session *taught me*, not what happened.

Category discipline:

- `user` — durable preferences, working style, role/context about the user. **Not** "the user asked me to do X today."
- `self` — identity-level shifts. Rare. Most go to `update_identity` instead.
- `collaboration` — patterns confirmed across multiple sessions about how we work best together.
- `lesson` — a mistake or surprise where I'd act differently next time. **Not** routine debugging.
- `reference` — durable pointers to people, accounts, tools, dashboards.

Aim for **zero or one** new memory per consolidation pass as the typical outcome. Three or more is a smell — re-read the bar above.
