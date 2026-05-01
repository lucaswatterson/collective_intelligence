---
description: Advance the user's read cursor in a Google Chat space so its
  messages no longer appear as unread. Sets `lastReadTime` to the current time
  by default, or to a caller-supplied RFC3339 timestamp. Read state is
  per-space, not per-message — calling this marks every message currently in
  the space as read. Requires `gws` to be installed and authenticated
  (`gws auth setup`).
input_schema:
  properties:
    space:
      type: string
      description: Space name (e.g. 'spaces/AAAAxxxx').
    last_read_time:
      type: string
      description: Optional RFC3339 timestamp to set as the new read cursor. If
        omitted, the current time is used. Useful when you want to mark up
        through a specific message's createTime.
  required:
  - space
  type: object
---

## Usage

    mark_chat_space_read(space="spaces/AAAAxxxx")
    mark_chat_space_read(
        space="spaces/AAAAxxxx",
        last_read_time="2026-05-01T15:30:00Z",
    )
