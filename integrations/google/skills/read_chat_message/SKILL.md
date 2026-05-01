---
description: Read the full content of a single Google Chat message by name.
  Use this when the snippet from `read_chat_unread` is truncated or you need
  the complete message including formatted text and any attachment metadata.
  Requires `gws` to be installed and authenticated (`gws auth setup`).
input_schema:
  properties:
    name:
      type: string
      description: Message name (e.g. 'spaces/AAAAxxxx/messages/YYY.YYY' — the
        first column from `read_chat_unread` output).
  required:
  - name
  type: object
---

## Usage

    read_chat_message(name="spaces/AAAAxxxx/messages/YYY.YYY")

Returns a block with the message metadata (sender, time, thread, space) and
the full text. Reading a message does NOT advance the space read cursor;
call `mark_chat_space_read` separately.
