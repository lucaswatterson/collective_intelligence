---
name: daily_review
at: "15:00"
enabled: false
created: null
last_run: null
task_title: Daily review
task_priority: medium
task_tags:
  - daily
  - review
author: harness
---

Reflect on today's activities. Review recent transcripts, note what went well, what surprised you, and any follow-ups worth capturing as long-term memories. Then call `complete_task`.

Schedule notes: `at: "15:00"` means this runs daily at 3PM in the system local timezone. To anchor to a specific zone, add `timezone: "America/Los_Angeles"` (any IANA name). A schedule must declare exactly one of `interval:` or `at:` — not both. Set `enabled: true` to activate.
