---
description: Reply to an existing Google Chat message in its thread. Use this —
  not `send_chat_message` — when responding to someone, otherwise the reply
  starts a new top-level thread. Pass the `space` and `thread` names taken
  directly from `read_chat_unread` output. Requires `gws` to be installed and
  authenticated (`gws auth setup`).
input_schema:
  properties:
    space:
      type: string
      description: Space name (e.g. 'spaces/AAAAxxxx').
    thread:
      type: string
      description: Thread name (e.g. 'spaces/AAAAxxxx/threads/YYY') of the
        message you are replying to.
    text:
      type: string
      description: Reply text (plain text; basic Chat markdown like *bold* and
        _italic_ is supported).
    dry_run:
      type: boolean
      description: If true, validate the request locally without sending.
        Default false.
  required:
  - space
  - thread
  - text
  type: object
---

## Usage

    reply_chat_message(
        space="spaces/AAAAxxxx",
        thread="spaces/AAAAxxxx/threads/YYY",
        text="Got it, thanks!",
    )

Returns a one-line confirmation including the new message name, or a clear
error string if `gws` is missing, unauthenticated, or rejects the request.
Replying does NOT mark the space as read — call `mark_chat_space_read`
afterward.
