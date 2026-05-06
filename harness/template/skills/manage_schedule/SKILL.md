---
description: Read or modify entity/SCHEDULE.md, the single file that drives when
  the worker fires each standing responsibility. Supports four actions — list,
  add, update, remove. Cadence is either a human interval ('1m', '12h', '1d')
  or a 5-field cron expression ('0 9 * * 1-5'); exactly one per entry.
input_schema:
  properties:
    action:
      description: Which operation to perform.
      enum:
      - list
      - add
      - update
      - remove
      type: string
    name:
      description: Unique entry id within the schedule. Required for add, update,
        remove.
      type: string
    responsibility:
      description: Stem of the responsibility file to inline when this entry
        fires (entity/responsibilities/<stem>.md). Required for add.
      type: string
    interval:
      description: Human-friendly interval like '30m', '4h', '1d', '1w'. Mutually
        exclusive with cron. Pass null in update to clear.
      type: string
    cron:
      description: Standard 5-field cron expression in UTC, e.g. '0 9 * * 1-5'
        for weekday 9am. Mutually exclusive with interval. Pass null in update
        to clear.
      type: string
    enabled:
      description: Disable an entry without removing it. Defaults to true on add.
      type: boolean
    guard:
      description: Optional name of a pre-flight predicate that runs before the
        worker enqueues a task for this entry. If the guard returns false, the
        entry's last_run snaps forward and no task (and no LLM call) is created.
        Use this for pollers that often have nothing to do — e.g. pair
        'manage_email' with 'gmail_has_unread'. Pass null on update to clear.
        Call action='list' to see registered guard names.
      type: string
  required:
  - action
  type: object
---

## When to use

`manage_schedule` is how you make a responsibility actually run. Creating a responsibility writes the contract; adding a schedule entry decides when the worker enqueues it as a concrete task.

## How firing works

Every poll, the worker walks SCHEDULE.md. For each enabled entry:
- **interval**: due if `now - last_run >= interval`.
- **cron**: due if the next cron firing after `last_run` is at or before `now`.

When due, the worker reads `entity/responsibilities/<responsibility>.md`, inlines its body into a fresh task, and snaps `last_run` to `now` — exactly one task per due entry, even if many periods elapsed (no flood after restarts).

## Action reference

- `list` — return all entries with cadence, last-run, and any attached guard. Also lists the guard names registered in this harness.
- `add` — register a new entry. Requires `name`, `responsibility`, and exactly one of `interval` / `cron`. Optionally takes `guard`. Newly added entries wait one full period before first fire.
- `update` — change cadence, enabled state, or guard. Pass `interval: null` (or `cron: null`) to switch from one to the other; pass `guard: null` to clear a guard.
- `remove` — delete an entry. The referenced responsibility file is untouched.

## Guards

A **guard** is a pre-flight predicate the worker runs *before* enqueueing a task for this entry. If the guard returns false, the entry's `last_run` snaps forward and no task is created — so no LLM call is spent on a check that has nothing to do.

Use a guard whenever the responsibility's first step is "look for X, exit cleanly if there's none." Example: `manage_email` reads unread mail, replies where appropriate, marks read. If the inbox is empty, the worker would still pay for a full Sonnet+thinking turn just to read "0 unread." Pairing the schedule entry with `guard: gmail_has_unread` skips the call when there's nothing to read.

Guards are discovered from `entity/guards/*.py` — each integration ships its own plugin module (e.g. Google Workspace installs `entity/guards/google.py`). A fresh harness with no integrations installed has an empty registry; that's expected, not an error. They are *named* — pass the string name to this skill, not a function. To see the current registry, run `action='list'`. Common pairings (when the matching integration is installed):

- `gmail_has_unread` ↔ a `manage_email` responsibility
- `gchat_has_unread` ↔ a `manage_chat` responsibility

If a guard subprocess errors, parses oddly, or otherwise fails, the harness fails *open* — it enqueues the task anyway. An LLM call is cheaper than a missed message. An unknown guard name also fails open with a warning in `worker.log`, which is why this skill validates guard names against the registry at edit time rather than only at fire time.

If your responsibility doesn't have a cheap CLI-level "anything to do?" check, omit the guard and let it fire normally.

## Notes

- Cron is interpreted in the harness's configured timezone (`SCHEDULER_TIMEZONE` env var; UTC by default). The current value is visible in startup logs / `harness/config.py`. Stored `last_run` timestamps remain UTC.
- Cron uses standard crontab day-of-week semantics: `0` or `7` = Sunday, `1` = Monday, …, `6` = Saturday. So `1-5` is Mon–Fri. Named tokens (`mon-fri`, `sat,sun`) also work and are unambiguous.
- Disabling (`enabled: false`) is preferable to removing for things you might want back — it preserves `last_run` so re-enabling doesn't immediately fire.
