---
description: List Google Chat spaces (DMs, group chats, named rooms) the user is
  a member of. Returns one row per space with its name (`spaces/<id>`), type,
  display name (or '(DM)' for direct messages), and last-active time. Use this
  to discover space ids before calling `read_chat_unread`, `send_chat_message`,
  or `mark_chat_space_read`. Note that group chats and DMs are not listed until
  at least one message has been exchanged. Requires `gws` to be installed and
  authenticated (`gws auth setup`).
input_schema:
  properties:
    max_results:
      type: integer
      description: Maximum number of spaces to return (default 50).
    filter:
      type: string
      description: Optional Chat API filter, e.g. 'spaceType = "SPACE"' to limit
        to named rooms, or 'spaceType = "DIRECT_MESSAGE"' for DMs only.
  required: []
  type: object
---

## Usage

    list_chat_spaces()
    list_chat_spaces(max_results=10)
    list_chat_spaces(filter='spaceType = "SPACE"')

Returns one line per space:

    <name> | <type> | <display_name_or_DM> | <last_active>
