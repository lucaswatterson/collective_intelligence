---
description: Read the full content of a single Gmail message by id, including
  headers (From, To, Cc, Subject, Date) and the plain-text body. Use this after
  `read_email` to get the actual message content before deciding how to respond —
  the snippet returned by `read_email` is only a short preview. Requires the `gws`
  CLI to be installed and authenticated (`gws auth setup`).
input_schema:
  properties:
    id:
      type: string
      description: Gmail message id (the first column from `read_email` output).
    html:
      type: boolean
      description: If true, return the HTML body instead of plain text. Default false.
  required:
  - id
  type: object
---

## Usage

    read_email_message(id="18f1a2b3c4d")
    read_email_message(id="18f1a2b3c4d", html=True)

Returns a block like:

    From: Alice <alice@example.com>
    To: you@example.com
    Subject: Project update
    Date: ...

    (full plain-text body here)

Reading a message does NOT mark it as read. Call `mark_email_read(ids=...)`
explicitly when done evaluating.
