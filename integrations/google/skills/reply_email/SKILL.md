---
description: Reply to a Gmail message by id, preserving the thread (sets
  In-Reply-To, References, and threadId automatically). Use this — not
  `send_email` — when responding to an existing message, otherwise the reply
  starts a new thread. Supports reply-all, CC/BCC, HTML bodies, draft mode,
  and dry-run. Requires `gws` to be installed and authenticated
  (`gws auth setup`).
input_schema:
  properties:
    message_id:
      type: string
      description: Gmail message id of the message you are replying to (the first
        column from `read_email`, or the same id passed to `read_email_message`).
    body:
      type: string
      description: Reply body. Plain text by default. If `html` is true, treat as
        an HTML fragment (no <html>/<body> wrapper needed).
    reply_all:
      type: boolean
      description: If true, reply to all recipients (uses `gws gmail +reply-all`).
        Default false.
    cc:
      type: string
      description: Additional CC address(es), comma-separated. Optional.
    bcc:
      type: string
      description: Additional BCC address(es), comma-separated. Optional.
    html:
      type: boolean
      description: If true, send `body` as HTML. Default false.
    draft:
      type: boolean
      description: If true, save as a draft instead of sending. Default false.
    dry_run:
      type: boolean
      description: If true, validate the request locally without sending or
        drafting. Default false.
  required:
  - message_id
  - body
  type: object
---

## Usage

    reply_email(message_id="18f1a2b3c4d", body="Thanks, got it!")
    reply_email(message_id="18f1a2b3c4d", body="Looping in Carol", cc="carol@example.com")
    reply_email(message_id="18f1a2b3c4d", body="Reply to everyone", reply_all=True)
    reply_email(message_id="18f1a2b3c4d", body="Draft reply", draft=True)
    reply_email(message_id="18f1a2b3c4d", body="Test", dry_run=True)

Returns a one-line confirmation including the new message id on success, or a
clear error string if `gws` is missing, unauthenticated, or rejects the
request. Replying does NOT automatically mark the original as read — call
`mark_email_read` afterward.
