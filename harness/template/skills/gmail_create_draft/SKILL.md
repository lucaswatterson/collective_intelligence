---
description: Create a Gmail draft. The draft appears in the Gmail UI for the
  user to review and send. Preferred over gmail_send_message when sending
  has not been explicitly authorised.
input_schema:
  type: object
  properties:
    to:
      description: Recipient email address (comma-separate multiple).
      type: string
    subject:
      description: Subject line.
      type: string
    body:
      description: Plaintext body of the message.
      type: string
    cc:
      description: Optional Cc recipients (comma-separated).
      type: string
    bcc:
      description: Optional Bcc recipients (comma-separated).
      type: string
    in_reply_to_message_id:
      description: Optional Gmail message ID being replied to. If set, the
        draft is threaded and gets correct In-Reply-To/References headers.
      type: string
    thread_id:
      description: Optional Gmail thread ID. Usually set alongside
        in_reply_to_message_id for replies.
      type: string
  required:
  - to
  - subject
  - body
---

## Usage

For a reply draft, pass both `in_reply_to_message_id` and `thread_id` so
Gmail threads the draft alongside the conversation.

The returned `draft_id` is the handle for `gmail_send_draft`. Record it
(e.g. in a task or note) if the draft is intended to be sent later —
`gmail_list_drafts` can also recover it. **When you later want to send,
use `gmail_send_draft` with that id — not `gmail_send_message`.** That
preserves any edits the user made in the Gmail UI.
