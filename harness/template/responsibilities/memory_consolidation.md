---
name: memory_consolidation
description: Reflect on recent sessions and distill only durable, decision-changing
  insights into long-term memory.
created: '2026-05-01T21:59:31.393259+00:00'
---

## Contract

1. Call `manage_memory` with `action: unconsolidated` to get the list of session stems that haven't been distilled yet (oldest first). If the result is "No unconsolidated sessions.", call `complete_task` and stop.
2. Cap this pass at 30 stems. If there are more, take the first 30 — the next tick picks up the rest.
3. Pull context once for the batch:
   - Call `manage_memory` with `action: list` to see the current INDEX.
   - `read_file` on `IDENTITY.md` so identity-shift judgments stay grounded.
4. For each stem in the batch:
   - `read_file` on `memory/short_term/<stem>.md` to read the transcript.
   - Decide whether anything durable came out of it. **The default answer is no.** Most sessions — especially short task sessions like chat/inbox checks — yield zero new memories.
   - For any insight that *does* clear the bar in Principles below: call `manage_memory` with `action: create`, or `action: update` if INDEX shows it's already covered (pass `add_source_sessions` so the reinforcement is recorded). Lead the body with a one-line gist; INDEX uses it.
   - If a real shift in who you are emerges, call `update_identity` (read `IDENTITY.md` first for the clobber guard).
   - Call `archive_session` on the stem. **Every stem in the batch gets archived**, including ones that produced no memory. A consolidated-but-unarchived session lingers in `short_term/` forever — `action: unconsolidated` won't re-show it (its stem is already in some memory's `source_sessions`), but the file stays there.
5. Call `complete_task`.

## Principles

The bar: a memory is worth keeping only if it answers **yes** to *"Will I make a different decision in a future session because this is in long-term memory?"* If the answer is no, maybe, or "it's nice context," archive without writing.

Tests to apply *before* writing a memory:

- **Durability.** Will this still be true and relevant in a month? One-off task details, transient state, "today the user asked X" — no.
- **Derivability.** Can I get this from `IDENTITY.md`, the codebase, or `git log`? If yes, don't duplicate it into memory.
- **Generality.** Is this a pattern I've seen *more than once*, or a stance the user explicitly stated as durable? A single occurrence is rarely enough — prefer `manage_memory` (`action: update`) on the second occurrence to lift confidence over `action: create` on the first.
- **Anti-noise.** "We worked on X today" / "fixed bug Y" / "reviewed PR Z" → no. The session transcript already records that. Memory is for what the session *taught me*, not what happened.

Category discipline:

- `user` — durable preferences, working style, role/context about the user. **Not** "the user asked me to do X today."
- `self` — identity-level shifts. Rare. Most go to `update_identity` instead.
- `collaboration` — patterns confirmed across multiple sessions about how we work best together.
- `lesson` — a mistake or surprise where I'd act differently next time. **Not** routine debugging.
- `reference` — durable pointers to people, accounts, tools, dashboards.

Aim for **zero or one** new memory per consolidation pass as the typical outcome. Three or more is a smell — re-read the bar above.
