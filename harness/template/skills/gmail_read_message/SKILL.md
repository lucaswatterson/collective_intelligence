---
description: Fetch a single Gmail message by ID and return headers plus the
  decoded plaintext body.
input_schema:
  type: object
  properties:
    message_id:
      description: Gmail message ID (from gmail_search_messages).
      type: string
  required:
  - message_id
---

## Usage

Returns full headers (From/To/Cc/Date/Subject/Message-ID), labels, and the
body as plaintext. HTML-only messages are stripped to text on a best-effort
basis. For multi-message conversations prefer `gmail_read_thread`.
