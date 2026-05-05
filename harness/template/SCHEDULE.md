---
entries:
- name: memory_consolidation
  responsibility: memory_consolidation
  interval: 12h
  enabled: true
  last_run: null
---

# Schedule

This file is the single source of truth for *when* my standing responsibilities run. Each entry references a responsibility by stem (`entity/responsibilities/<stem>.md`); when its cadence is due, the worker reads that responsibility and inlines its body into a fresh task in `entity/tasks/`.

Editing rules:

- Use `manage_schedule` to add, update, or remove entries — it validates cadence and that the responsibility exists.
- Cadence is **either** `interval` (e.g. `1m`, `12h`, `1d`) **or** `cron` (5-field, UTC, standard crontab semantics with `0`/`7` = Sunday) — exactly one per entry.
- `last_run` is "last enqueued," maintained by the worker. A `null` value means "never fired yet"; the entry will be initialized on first sight and fire after one full period.
- `enabled: false` keeps the entry on the books without firing it.
- Catch-up is fire-once: a long offline period produces one task per overdue entry, not a flood.
