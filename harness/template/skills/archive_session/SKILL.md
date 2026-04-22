---
description: Move a short-term session transcript from entity/memory/short_term/
  to entity/memory/short_term_archive/ after it has been consolidated into long-term
  memory. Idempotent — already-archived sessions return success.
input_schema:
  properties:
    session:
      description: Session stem or filename (e.g. '2026-04-19T14-22-01' or '2026-04-19T14-22-01.md').
        Partial matches are supported if unambiguous.
      type: string
  required:
  - session
  type: object
---

## Usage

- Call once per session after you've captured its lasting content via `create_memory` / `update_memory`.
- The archive lives alongside the live dir: `entity/memory/short_term_archive/`. It is searchable but not injected as context on future sessions.
- Never call on a session you haven't consolidated — that session's transcript will no longer be considered "unconsolidated" by future `consolidate_memory` calls.
