---
description: Mark one or more Gmail messages as read by removing the UNREAD
  label. Call this after evaluating unread messages — including ones you decided
  not to reply to — so they don't show up the next time `read_email` is called.
  Requires `gws` to be installed and authenticated (`gws auth setup`).
input_schema:
  properties:
    ids:
      description: A single Gmail message id (string), or a list of ids. Each id
        is the first column from `read_email` output.
      anyOf:
        - type: string
        - type: array
          items:
            type: string
  required:
  - ids
  type: object
---

## Usage

    mark_email_read(ids="18f1a2b3c4d")
    mark_email_read(ids=["18f1a2b3c4d", "18f1a2b3c4e", "18f1a2b3c4f"])

A single id uses the per-message endpoint; multiple ids use `batchModify` for
efficiency. Returns `Marked N message(s) read: <id1>, <id2>, ...` on success.
