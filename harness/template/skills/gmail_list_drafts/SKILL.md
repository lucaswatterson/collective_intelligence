---
description: List Gmail drafts with their draft IDs, recipients, and subjects.
  Use to enumerate drafts pending review/send across tasks and sessions.
input_schema:
  type: object
  properties:
    query:
      description: Optional Gmail search query to filter drafts (e.g. "to:alice@example.com").
        Empty/omitted lists all drafts.
      type: string
    max_results:
      description: Maximum number of drafts to return. Defaults to 20, max 100.
      type: integer
---

## Usage

Each entry leads with the **draft id** — that's the handle
`gmail_send_draft` consumes. The underlying message id and thread id are
also shown (useful for reading the full draft body via
`gmail_read_message`).

Typical flow:
1. `gmail_list_drafts` — find pending drafts.
2. `gmail_read_message` on each draft's message id — inspect what will be sent.
3. `gmail_send_draft` with the draft id — send it as-is (preserving any edits the user made in Gmail).
