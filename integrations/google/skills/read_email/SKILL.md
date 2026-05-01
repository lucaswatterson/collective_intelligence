---
description: List unread emails from the user's Gmail inbox as a triage summary.
  Returns one line per message with the Gmail message id, date, sender, subject, and
  a short snippet preview. Requires the `gws` CLI to be installed and authenticated
  (`gws auth setup`).
input_schema:
  properties:
    max_results:
      description: Maximum number of unread messages to return (default 20).
      type: integer
  required: []
  type: object
---

## Usage

Returns one line per unread message:

    <id> | <date> | <sender> | <subject> — <snippet preview>

Example:

    read_email()
    read_email(max_results=10)

## Important — the snippet is NOT the message

The snippet is a short preview (≤120 chars) and is often truncated mid-sentence.
**Do not decide whether to respond based on the snippet alone.** Before replying
to or judging a message, call `read_email_message(id=...)` with the id from the
first column to fetch the full headers and body.

After evaluating a batch of unread mail, call `mark_email_read(ids=[...])` so
the same messages don't show up next time — including ones you decided not to
reply to.

If `gws` is not installed or not authenticated, the skill returns an error
message with the exact shell command to fix it.
