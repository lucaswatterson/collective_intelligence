---
description: Send an existing Gmail draft by its draft ID. Use this to send
  drafts created earlier via gmail_create_draft — do NOT re-compose with
  gmail_send_message.
input_schema:
  type: object
  properties:
    draft_id:
      description: The draft ID returned by gmail_create_draft or gmail_list_drafts.
      type: string
  required:
  - draft_id
---

## Usage

This sends whatever currently exists as the draft in Gmail — including
any edits the user made in the Gmail UI after the draft was created.
That's the point: the human-in-the-loop review step is preserved.

If the draft has been deleted or never existed the Gmail API returns an
error (typically `draftNotFound`); that error is returned verbatim so
the caller can decide whether to recreate it or abandon the send.
