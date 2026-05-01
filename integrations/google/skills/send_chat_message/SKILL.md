---
description: Send a new top-level Google Chat message to a space (starts a new
  thread). Use this for unsolicited messages or new topics. To respond to an
  existing message in its thread, use `reply_chat_message` instead. Requires
  `gws` to be installed and authenticated (`gws auth setup`).
input_schema:
  properties:
    space:
      type: string
      description: Space name (e.g. 'spaces/AAAAxxxx'). Use `list_chat_spaces`
        to find it.
    text:
      type: string
      description: Message text (plain text; basic Chat markdown like *bold*
        and _italic_ is supported).
    dry_run:
      type: boolean
      description: If true, validate the request locally without sending.
        Default false.
  required:
  - space
  - text
  type: object
---

## Usage

    send_chat_message(space="spaces/AAAAxxxx", text="Heads up: deploy in 10")
    send_chat_message(space="spaces/AAAAxxxx", text="test", dry_run=True)

Returns a one-line confirmation on success, or an error string if `gws` is
missing, unauthenticated, or rejects the request.
