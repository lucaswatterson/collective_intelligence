---
description: Modify a Gmail message's labels. Covers archive, mark
  read/unread, and arbitrary label add/remove in one operation.
input_schema:
  type: object
  properties:
    message_id:
      description: Gmail message ID to modify.
      type: string
    add_label_ids:
      description: Label IDs to add. Use gmail_list_labels to resolve names.
      type: array
      items:
        type: string
    remove_label_ids:
      description: Label IDs to remove.
      type: array
      items:
        type: string
    archive:
      description: If true, removes the INBOX label (archives the message).
      type: boolean
    mark_read:
      description: If true, removes UNREAD. If false, adds UNREAD (marks unread).
        Omit to leave read-state alone.
      type: boolean
  required:
  - message_id
---

## Safety

Label/archive/read-state changes are reversible but immediately visible to
the user in Gmail. When you make these changes, say what you did — don't
silently mutate the inbox.
