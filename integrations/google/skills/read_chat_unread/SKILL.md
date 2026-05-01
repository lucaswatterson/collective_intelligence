---
description: Find unread Google Chat messages across all spaces (or one named
  space). For each space, looks up the user's last-read time via spaceReadState
  and lists messages created after it. Returns one row per unread message with
  the message name, thread name, time, sender, and a text snippet. Use the
  message and thread names from this output to call `reply_chat_message` or
  `read_chat_message`. Requires `gws` to be installed and authenticated
  (`gws auth setup`).
input_schema:
  properties:
    space:
      type: string
      description: Optional space name (e.g. 'spaces/AAAAxxxx') to limit the
        check to one space. If omitted, scans every space the user is in.
    max_spaces:
      type: integer
      description: Maximum number of spaces to scan when `space` is not provided
        (default 50).
    max_messages_per_space:
      type: integer
      description: Maximum unread messages to return per space (default 20).
  required: []
  type: object
---

## Usage

    read_chat_unread()
    read_chat_unread(space="spaces/AAAAxxxx")
    read_chat_unread(max_spaces=20, max_messages_per_space=10)

Returns a section per space that has unread messages:

    === spaces/AAAAxxxx (DIRECT_MESSAGE) — 3 unread since 2026-04-24T18:40:54Z ===
    <message_name> | <thread_name> | <createTime> | <sender_name> | <text snippet>
    ...

Spaces with zero unread are omitted. The text snippet is truncated to ~200
chars; call `read_chat_message(name=...)` for full content. After evaluating,
call `mark_chat_space_read(space=...)` to advance the read cursor — note that
read state is per-space, not per-message, so marking advances past every
message you just listed.
