# Google Workspace Integration

Opt-in skills that give the entity access to the user's Google Workspace via the
[`gws` CLI](https://github.com/googleworkspace/cli). The harness itself does not
depend on this directory — it is a template tree that gets copied into
`entity/skills/` by an install script.

## Prerequisites

1. Install the CLI:
   ```
   brew install googleworkspace-cli
   ```
2. Authenticate once:
   ```
   gws auth setup
   ```
   `gws` owns the OAuth lifecycle and persists credentials under `~/.config/gws/`.
   The harness never touches Google credentials directly.

## Install the skills

```
uv run scripts/install_google_workspace.py
```

This copies every skill folder under `integrations/google/skills/` into
`entity/skills/` and reports whether `gws` is on `PATH`. Skills that are already
installed are skipped — pass `--force` to overwrite them when the templates
change:

```
uv run scripts/install_google_workspace.py --force
```

Restart the entity (or invoke `list_skills` from the TUI) to pick up new or
updated skills.

## Available skills

Two parallel skill sets — Gmail and Chat — each covering the same
triage-and-respond loop: discover unread, read full content, reply where
appropriate, mark read.

### Gmail

- **`read_email`** — wraps `gws gmail +triage --format json` and returns a
  compact unread-inbox summary, one row per message:
  `<id> | <date> | <sender> | <subject> — <snippet>`. Accepts an optional
  `max_results` integer (default 20). The snippet is a short preview only;
  use `read_email_message` for the full body.
- **`read_email_message`** — wraps `gws gmail +read --id <ID> --headers
  --format json`. Returns headers (`From`, `To`, `Cc`, `Subject`, `Date`) plus
  the plain-text body. Pass `html=true` to get the HTML body instead. Reading
  does NOT mark a message as read.
- **`reply_email`** — wraps `gws gmail +reply --message-id <ID> --body <TEXT>`
  (or `+reply-all` when `reply_all=true`). Preserves threading via
  `In-Reply-To`/`References`/`threadId`. Supports `cc`, `bcc`, `html`, `draft`,
  and `dry_run`. Use this — not `send_email` — when responding to an existing
  thread.
- **`send_email`** — wraps `gws gmail +send`. Use for new outbound messages
  that are not replies.
- **`mark_email_read`** — removes the `UNREAD` label from one message
  (`users.messages.modify`) or many (`users.messages.batchModify`). Accepts
  either a single id string or a list. Call after evaluating a batch of unread
  mail, including messages you decided not to reply to.

### Google Chat

Chat tracks read state per **space**, not per message — there is no Gmail-style
UNREAD label on individual messages. "Unread" means messages whose `createTime`
is later than the user's `spaceReadState.lastReadTime`. Marking-as-read
advances that cursor for the whole space at once.

- **`list_chat_spaces`** — wraps `gws chat spaces list`. Returns one row per
  space (DMs, group chats, named rooms) with `<name> | <type> | <display> |
  <last_active>`. Group chats and DMs only appear after the first message has
  been exchanged.
- **`read_chat_unread`** — for each space (or one named via `space=...`), looks
  up `spaceReadState.lastReadTime` and lists messages newer than it. Output is
  grouped by space, one row per message:
  `<message_name> | <thread_name> | <createTime> | <sender> | <text snippet>`.
  Snippet is truncated to ~200 chars; use `read_chat_message` for full text.
- **`read_chat_message`** — wraps `gws chat spaces messages get`. Returns full
  metadata and text for a single message by name.
- **`reply_chat_message`** — wraps `gws chat spaces messages create` with
  `messageReplyOption=REPLY_MESSAGE_OR_FAIL` and `thread.name` set, so the
  reply lands in the same thread. Pass `space` and `thread` straight from
  `read_chat_unread` output.
- **`send_chat_message`** — wraps `gws chat +send`. Posts a new top-level
  message in a space (starts a new thread).
- **`mark_chat_space_read`** — wraps `gws chat users spaces
  updateSpaceReadState`. Sets `lastReadTime` to now (or a caller-supplied
  RFC3339 timestamp). Affects the whole space — there's no per-message
  read flag in the Chat API.

## Schedule guards

This integration ships two pre-flight guards alongside the skills (defined in
`integrations/google/guards.py` and copied to `entity/guards/google.py` by the
install script above). The harness discovers them from `entity/guards/` at
runtime, so they only register on harnesses where this integration is
installed. Attach one to a schedule entry via `manage_schedule`'s `guard:`
parameter to skip the entire LLM turn when there's nothing to triage:

- **`gmail_has_unread`** — runs `gws gmail +triage --max 1` and returns true
  iff at least one unread message comes back. Pair with a `manage_email`
  responsibility.
- **`gchat_has_unread`** — lists Chat spaces and stops on the first space
  whose newest message is later than its `spaceReadState.lastReadTime`. Pair
  with a `manage_chat` responsibility.

Both fail open (errors enqueue the task anyway), so a flaky `gws` call won't
silently swallow a real message. Add them when registering the schedule
entry — e.g. `manage_schedule action=add name=manage_email
responsibility=manage_email cron='*/30 8-20 * * 1-5' guard=gmail_has_unread`.

## Removing the integration

Delete the copied skill directories and the guards plugin:

```
rm -rf entity/skills/read_email/ entity/skills/read_email_message/ \
       entity/skills/reply_email/ entity/skills/send_email/ \
       entity/skills/mark_email_read/ \
       entity/skills/list_chat_spaces/ entity/skills/read_chat_unread/ \
       entity/skills/read_chat_message/ entity/skills/reply_chat_message/ \
       entity/skills/send_chat_message/ entity/skills/mark_chat_space_read/
rm -f  entity/guards/google.py
```

The entity loses Google access on next skill rediscovery, and the
`gmail_has_unread` / `gchat_has_unread` guards drop out of the registry
the next time `load_guards()` runs. Nothing under `harness/` needs to change.
