---
description: Compose and send a NEW email from the authenticated Gmail
  account. Use only for fresh composition. To send an existing draft,
  call gmail_send_draft with the draft id — do NOT re-author with this
  skill. Prefer gmail_create_draft unless sending has been explicitly
  authorised.
input_schema:
  type: object
  properties:
    to:
      description: Recipient email address (comma-separate multiple).
      type: string
    subject:
      description: 'Subject line. For replies this is typically "Re: <original subject>".'
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
        outgoing message is threaded and gets correct In-Reply-To/References headers.
      type: string
    thread_id:
      description: Optional Gmail thread ID to attach the message to. Usually
        set alongside in_reply_to_message_id.
      type: string
  required:
  - to
  - subject
  - body
---

## Safety

Do NOT send on behalf of the user without explicit confirmation in the
current task or conversation. When in doubt, call `gmail_create_draft`
instead — drafts are reviewable in the Gmail UI before they go out.

**To send a draft that already exists, call `gmail_send_draft` with the
draft id — do not re-compose with this skill.** Re-composing bypasses any
edits the user made to the draft in Gmail.

## Usage

For a reply, pass both `in_reply_to_message_id` (the Gmail message ID of
the message being replied to) and `thread_id` so Gmail threads the
conversation correctly. The skill resolves the original RFC 822
`Message-ID` header automatically.
