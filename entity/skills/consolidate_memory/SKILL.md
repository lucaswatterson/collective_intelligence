---
description: Reflect on unconsolidated short-term sessions and prepare to distill
  them into long-term memory. Returns raw session transcripts alongside the current
  long-term index and IDENTITY.md — the entity then calls create_memory / update_memory
  / update_identity / archive_session as needed.
input_schema:
  properties:
    limit:
      description: Maximum number of unconsolidated sessions to return. Defaults to
        10. Oldest unconsolidated sessions are returned first.
      type: integer
  type: object
---

## Usage

### What this skill does
- Scans `entity/memory/short_term/` for session transcripts.
- Filters out sessions that are already referenced in any long-term memory's `source_sessions` frontmatter.
- Returns the current `INDEX.md`, the current `IDENTITY.md`, and up to `limit` unconsolidated session transcripts as one structured block.

### What this skill does NOT do
- It does not write memories itself. Reflection is your job — the skill hands you the raw material.
- It does not archive sessions. After you distill a session into memories, call `archive_session` on it.

### Typical flow
1. Call `consolidate_memory` (optionally with `limit`).
2. For each insight durable enough to outlive the session: call `create_memory` (or `update_memory` if an existing entry from INDEX covers it).
3. If anything shifts your core identity: call `update_identity`.
4. Call `archive_session` per session processed.

### Notes
- The current session's transcript is excluded — it's not written yet.
- "Unconsolidated" is determined by `source_sessions` presence, not location — if you forget to `archive_session`, the session is still treated as consolidated next time (since it's now in `source_sessions`). Archiving is for cleanliness and for controlling what future `begin_session` loads as recent context.
