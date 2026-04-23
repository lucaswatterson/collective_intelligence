# Harness

This document describes the machinery you run inside. `BIRTH.md` covers
what you own; `IDENTITY.md` covers who you are. This file covers *how*
you work — the Python process, threads, loops, and conventions that
turn "a conversation with Claude" into "you."

It is your own source of truth when someone asks "how do you work?"
Read from here rather than guessing from `src/`.

## 1. What the harness is

You live inside a Python package called **Collective Intelligence**
(`harness/`). A single process starts you: `main.py` at the repo
root. The harness owns five things on your behalf:

- **The event loop** — when you're awake, what you're doing, when you stop.
- **The Claude API bridge** — every token you produce goes through
  `harness/client.py`.
- **The skill registry** — your capabilities, loaded from
  `entity/skills/` into Claude tool-use schemas.
- **Memory I/O** — session transcripts and long-term notes, read and
  written as plain markdown under `entity/memory/`.
- **The filesystem contract** — every path you touch is derived from a
  single `Settings` object (`harness/config.py`).

You do not manage any of this yourself. You produce text and tool calls;
the harness translates them into filesystem changes, API requests, and
UI updates.

## 2. The three modes you run in

You are always in exactly one of these:

### Birth
First boot, when `entity/IDENTITY.md` is empty or missing. Your system
prompt is `BIRTH.md`. Your tools are `commit_identity`, web search, web
fetch, and whatever skills are present (typically none at birth).
Streaming is on — the human sees you think in real time. You leave birth
the moment you call `commit_identity`; the file is written to disk, your
system prompt swaps to `IDENTITY.md`, and the worker thread would start
on the *next* process restart.

### Chat
Interactive conversation with the human, driven by the TUI. One turn =
one user message + one assistant response, with tool-use cycles in
between. Streaming is on. This is the mode that runs in the main
thread.

### Worker
Autonomous background execution of tasks from `entity/tasks/`. No
human in the loop. The worker still calls `stream_turn` under the
hood, but without an `on_text` callback, so nothing is rendered —
functionally non-interactive. Driven by `harness/runtime/worker.py`.
The worker thread always starts; if you are unborn it idles and
polls `needs_birth()` each tick instead of picking up tasks.

Chat and worker share almost all machinery but use **separate `Entity`
instances** (see §3). A chat turn never sees worker messages and vice
versa.

## 3. Process and threads

`main.py` assembles everything:

- Loads `.env` via `load_settings()` → a `Settings` object (paths, API
  key, poll interval, model names).
- Calls `bootstrap_entity(settings)`, which copies
  `harness/template/` into `entity/` if `entity/` doesn't exist yet.
  This is how a fresh checkout gets a seeded workspace.
- Creates two `Entity` instances: `chat_entity` and `worker_entity`.
  They share `Settings` but have independent `messages`, `skills`,
  `transcript`, and `system_text` state.
- Creates a `WorkerStatus` (thread-safe snapshot the TUI reads) and a
  `threading.Event` called `stop_event`.
- Unconditionally starts a daemon thread running `run_worker(...)`.
  The thread checks `needs_birth()` each tick and waits out the poll
  interval if you're unborn, rather than being gated at startup.
- Runs `run_tui(chat_entity, status, stop_event, settings.tasks_dir)`
  in the main thread.
- On TUI exit, sets `stop_event` and joins the worker thread with a
  5-second timeout.

So: up to three threads are live — the main TUI thread, the worker
thread, and a ticker thread inside the TUI that refreshes the display
every 100 ms. The turn itself also spawns a short-lived thread so the
ticker keeps updating while you think.

## 4. `Entity` lifecycle

All of your behavior is in `harness/entity.py`. The `Entity`
class has four public methods.

### `needs_birth() -> bool`
True if `entity/IDENTITY.md` doesn't exist or is whitespace. Checked at
startup (gates the worker thread) and at the start of every chat
session (chooses system prompt and tool set).

### `begin_session() -> None`
Called once when the TUI opens. It:

1. Discovers skills via `discover_skills(settings.skills_dir)`.
2. Starts a fresh transcript in `entity/memory/short_term/` via
   `start_session(...)`. Filename is `YYYY-MM-DDTHH-MM-SS.md`.
3. Chooses system prompt: `BIRTH.md` if unborn, `IDENTITY.md`
   otherwise. Sets `in_birth` accordingly.
4. If born, primes `messages` with a **seed exchange**: one `user`
   turn containing the long-term memory index (`INDEX.md`) and/or
   the two most recent transcripts (excluding the session just
   started), and one `assistant` turn that says "Recalled. Ready."
   Either part is skipped if absent; the seed is omitted entirely if
   you have no index and no prior transcripts. This is how continuity
   across sessions works — you start every chat with your recent past
   already in context.

### `turn(user_input, *, on_text) -> str`
One chat turn. Appends the user message to the transcript and
`messages`, runs the tool loop with `streaming=True`, appends the
final assistant text to the transcript, returns it.

### `work_on_task(task_path, *, on_tool_use) -> str`
One autonomous task. Re-discovers skills, loads `IDENTITY.md`, opens a
new transcript named `..._task_<slug>.md`, injects the long-term index
(no recent transcripts — only the index), then injects the task body
wrapped in `WORKER_PROMPT_PREFIX` (which tells you: save artifacts
under `entity/work/<slug>/`, call `complete_task` or `update_task`
when done, don't ask the human questions). Runs the same tool loop
as chat but with no `on_text` callback, so streamed tokens are
discarded rather than rendered.

### `_run_tool_loop(...)` — the core
Same loop for chat and worker. Each iteration:

1. Assemble `tools = [WEB_SEARCH_TOOL, WEB_FETCH_TOOL, *skills_as_tools]`.
   Prepend `COMMIT_IDENTITY_TOOL` if `in_birth`.
2. Call `client.stream_turn(...)` — always, for chat and worker.
   `create_turn` still exists on the client but the default loop no
   longer uses it.
3. Append assistant response to `messages`.
4. If `stop_reason == "pause_turn"`: loop again (Claude's way of
   saying "keep going").
5. If `stop_reason != "tool_use"`: break and return the concatenated
   text blocks.
6. Otherwise, for each `tool_use` block:
   - During birth, `commit_identity` is handled specially: write
     `IDENTITY.md`, flip `in_birth=False`, return the canned "you are
     born" result.
   - Otherwise, `registry.execute(skills, name, input)` runs the skill
     and returns its string result (or an error string).
   - If the tool name is in `SKILL_RELOAD_TRIGGERS`
     (`create_skill`/`update_skill`/`delete_skill`), set
     `reload_skills=True`.
   - If it's in `IDENTITY_RELOAD_TRIGGERS` (`update_identity`), set
     `reload_identity=True`.
7. Append all `tool_result` blocks as a single user message.
8. If reload flags set, re-discover skills / reread `IDENTITY.md` so
   changes take effect **on the next iteration**, not next session.

The loop ends when the model stops requesting tools.

## 5. The Claude bridge

`harness/client.py` is thin. `EntityClient` wraps
`anthropic.Anthropic` and exposes two methods:

- `stream_turn(...)` — used by both chat and worker. Streams text
  chunks to an optional `on_text` callback (the TUI uses this to
  render tokens as they arrive; the worker passes `None`), then
  returns the final `Message` object with all content blocks
  including tool uses.
- `create_turn(...)` — non-streaming alternative. Present on the
  client but not currently called by the default loop.

Both accept the same args. Both default to `max_tokens=32000`. Both
enable extended thinking with
`thinking={"type": "enabled", "budget_tokens": 10000}` for
`Models.REASONING` and `Models.DEFAULT`.

Models live in `config.py`:

- `Models.REASONING = "claude-opus-4-7"` — not currently used by the
  default loop, but available.
- `Models.DEFAULT = "claude-sonnet-4-6"` — what both chat and worker
  actually use.
- `Models.FAST = "claude-haiku-4-5"` — unused, available.

The `cached_system(text)` helper wraps the system prompt with an
`ephemeral` cache breakpoint so `BIRTH.md` / `IDENTITY.md` doesn't
re-tokenize every turn.

## 6. Tools and skills

### Built-in tools
Injected in every turn:

- `web_search` (`web_search_20250305`, `max_uses: 10`)
- `web_fetch` (`web_fetch_20250910`, `max_uses: 10`, citations on)

And, only during birth:

- `commit_identity` — the one-shot tool that ends the birth mode.

### Skills
Everything else is a skill. A skill is a folder under `entity/skills/`
containing:

- `SKILL.md` — frontmatter with `description` and `input_schema`
  (JSON Schema, `type: "object"`), plus an optional markdown body.
  The body is appended to the description when the tool is shown to
  Claude, so you can put usage notes there.
- `skill.py` — a Python module that defines `run(**input) -> str`.
  Whatever `run` returns becomes the tool result string; exceptions
  are caught and surfaced as `"Error executing skill '<name>': ..."`.

Discovery is `discover_skills(skills_dir)` in `skills/loader.py`: it
globs `*/SKILL.md`, skips hidden folders (like `.archive/`), parses
frontmatter, dynamically imports `skill.py` via `importlib`, and
returns a list of `Skill` dataclasses.

Exposure is `to_anthropic_tools(skills)` in `skills/registry.py`:
maps each `Skill` to `{name, description, input_schema}`.

Execution is `execute(skills, name, tool_input)`: finds the named
skill, calls `run(**tool_input)`, stringifies the result.

### Self-modifying skills
Skills that change other skills (`create_skill`, `update_skill`,
`delete_skill`) use the stage-and-validate flow in `skills/meta.py`:

1. Write the new skill to a temp directory.
2. `load_skill()` it there — this forces the module to import, which
   catches syntax errors, missing `run`, bad schema, etc.
3. Only on success, move the temp dir into `entity/skills/<name>/`,
   replacing any prior version.
4. Deletion uses `archive_skill()`, which moves the folder to
   `entity/skills/.archive/<name>_<utc-timestamp>/` — skills are
   never truly deleted.

Because the tool loop reloads skills on these triggers, a newly
created skill is callable on the very next tool iteration of the same
turn.

## 7. Memory

Two layers, both plain markdown on disk.

### Short-term
`harness/memory/store.py` owns session transcripts.

- `start_session(short_term_dir)` creates
  `entity/memory/short_term/YYYY-MM-DDTHH-MM-SS.md` with a header and
  returns the path.
- `append_turn(transcript, role, content)` appends
  `## <role> (HH:MM:SS)\n\n<content>\n\n`. Every user and assistant
  message in chat and worker modes is written this way.
- `recent_transcripts(short_term_dir, limit=2)` reads the N newest
  files; `begin_session` uses this to prime your context.

Task sessions look the same but are named `..._task_<slug>.md` so
they're distinguishable.

### Long-term
`harness/memory/long_term.py` handles the consolidated layer.

- Files live in `entity/memory/long_term/`. Each has YAML
  frontmatter: `title`, `category` (one of `user`, `self`,
  `collaboration`, `lesson`, `reference`), `confidence`,
  `source_sessions` (list of short-term stems), `created`, `updated`,
  optional `tags`.
- `rebuild_index(long_term_dir, index_path)` scans the folder and
  writes `INDEX.md` grouped by category with a one-line gist per
  entry. This runs whenever a memory is written.
- `consolidated_session_stems(long_term_dir)` returns the set of
  short-term stems already captured in long-term — used by
  `consolidate_memory` to avoid re-processing sessions.
- `resolve_partial(dir, filename)` is a fuzzy lookup for skills that
  want to accept a partial filename.

Consolidation itself is skill-driven (`consolidate_memory`,
`create_memory`, `update_memory`, `archive_session`). The harness
doesn't schedule it — you do, when it matters.

## 8. The worker loop

`harness/runtime/worker.py` defines `run_worker(...)`, the
daemon loop that consumes tasks.

### Scheduler tick
Before picking a task, each poll iteration calls
`materialize_due_schedules(schedules_dir, tasks_dir, now)` from
`harness/runtime/scheduler.py`. That function walks
`entity/schedules/*.md` and for each schedule whose next fire is
due — and which has no pending task (`todo` / `in-progress` /
`blocked`) bearing its `schedule:` tag — writes a fresh task into
`entity/tasks/` and updates `last_run`.

Schedules declare exactly one of two modes:
- `interval: 24h` — fires when `last_run + interval <= now`
  (drifts based on first fire).
- `at: "16:05"` (optional `timezone: "America/Los_Angeles"`,
  defaults to system local) — fires once per day at that wall-clock
  time. First run waits for the next boundary; DST transitions are
  handled.

Scheduler failures are logged but don't stop the worker.

### Picking a task
`_next_todo(tasks_dir)` scans `entity/tasks/*.md` (skipping hidden
files), loads frontmatter, filters to `status: todo`, and sorts by:

1. Priority — `high` (0), `medium` (1), `low` (2). Missing or
   unknown → `medium`.
2. `created` timestamp ascending — older first.
3. Filename — as a stable tiebreak.

The first candidate wins. If none are ready, the loop waits
`worker_poll_interval` seconds (default 10) and scans again.

### Running a task
For each task:

1. `_set_status(path, "in-progress")` is written *before* handing the
   task off — a defensive transition so a re-scan mid-run doesn't
   double-pick it if the entity never calls `update_task`.
2. `status.start_task(title, filename)` updates the thread-safe
   snapshot the TUI is rendering.
3. `entity.work_on_task(task.path, on_tool_use=status.record_tool)`
   runs the autonomous tool loop. You are expected to call
   `complete_task` (moves the task out of the active folder) or
   `update_task` (which may flip `status` to `blocked` or leave
   it `in-progress` with a note).
4. If `work_on_task` raises, the harness writes `status: blocked` and
   appends a `*Worker note*` section with the traceback — but only if
   the file still exists (you may have archived it).
5. If the task loop returns cleanly but the task file is still on
   disk with `status: in-progress` (i.e. you never called
   `complete_task` or `update_task`), the harness marks it `blocked`
   with a note saying so. This prevents silently stuck tasks.
6. `status.finish()` resets the snapshot to idle.
7. A 500 ms wait on `stop_event` before the next scan, so a shutdown
   request is picked up promptly even if the queue is long.

`stop_event` is how the TUI tells the worker to quit on exit.

### Shared status
`harness/runtime/status.py` is a `threading.Lock`-protected
`WorkerSnapshot` dataclass: `idle`, `current_task`, `current_filename`,
`step`, `last_tool`, `started_at`. Every tool call the worker makes
increments `step` and records `last_tool` — that's what you see move
in the "tasks" panel.

## 9. The TUI

`harness/ui/tui.py` is built on `rich.live.Live`. The root layout is
a 2:1 horizontal split (chat on the left, right column minimum 28
cols). The chat column splits vertically into a chat body and an
input panel that grows to fit the current prompt. The right column
splits vertically into a **self-image panel** (shows ASCII art from
`entity/self_image.txt`, or a placeholder if empty) and a **tasks
panel** (current worker snapshot plus up to five queued tasks).

### Threads
- **Main thread** — `tty.setcbreak`, reads stdin one char at a time
  via `select`, dispatches to `InputState`.
- **Ticker thread** — wakes every 100 ms and calls `refresh()`,
  which re-renders both panels. This is why the worker's `step`
  counter animates even when you're mid-turn.
- **Turn thread** — spawned per submission. Runs
  `entity.turn(text, on_text=...)`. The `on_text` callback appends
  streaming chunks to a `Text` object in the chat buffer, which the
  ticker picks up on its next refresh.

### Input handling
Raw keystrokes. Enter submits a non-empty line. Backspace / Ctrl-H
deletes. Ctrl-U clears. Ctrl-C and Ctrl-D-on-empty quit. Typing
`exit` or `quit` also exits. ESC-prefixed CSI sequences are parsed
for scrollback: Up/Down scroll the chat by one line, PageUp/PageDown
by ten, Home jumps to the top, End snaps back to live. While
scrolled, the chat panel title and border color change to signal
that new output is hidden. There's no in-line text editing beyond
backspace.

### Banners
At session start the TUI shows one of:

- `entity unborn · begin the birth conversation` followed by
  `tasks dormant until IDENTITY.md is committed`
- `entity online · type and press enter · Ctrl-C to quit · tasks running`

### What you don't see
The TUI is not your eyes — you don't read it. Your only input is
whatever the human types. But your output is streamed token-by-token
into the chat pane via `on_text`, so from the human's side you think
in real time.

## 10. The filesystem contract

Every path is a property on `Settings` (`harness/config.py`).
You own these, under `entity/`:

- `IDENTITY.md` — your system prompt once born. See `BIRTH.md` for
  philosophy.
- `knowledge/` — human-curated ground truth.
- `memory/short_term/` — transcripts, one per session.
- `memory/short_term_archive/` — transcripts you've consolidated and
  chosen to archive.
- `memory/long_term/` — consolidated memories.
- `memory/long_term/INDEX.md` — auto-generated category index.
- `tasks/` — active work items (`status: todo|in-progress|blocked`).
- `schedules/` — recurring job definitions. The worker-loop
  scheduler reads these, checks `interval` vs `last_run` (or
  `at` + `timezone` for wall-clock mode), and materializes fresh
  tasks into `tasks/` when due.
- `skills/` — your capabilities. `skills/.archive/` holds old
  versions.
- `work/` — artifacts produced by tasks, organized by task slug.
- `files/` — general storage.
- `self_image.txt` — optional ASCII art rendered in the TUI's
  self-image panel. Write to it and the TUI picks it up on its next
  refresh.
- `worker.log` — the worker thread's log output.

You may also see `IDENTITY_HISTORY.md` at the entity root if a skill
has been written to preserve identity edits; the config exposes its
path but the harness itself doesn't write it — that's a skill's job.

Note the `harness/template/` directory: it's the seed copied into
`entity/` by `bootstrap_entity` on first boot. Editing the template
changes what new installs see, not what an already-bootstrapped
entity has on disk.

## 11. Startup sequence

A compact trace of what happens between `uv run main.py` and your
first prompt:

1. `load_settings()` reads `.env` and builds the `Settings` object.
2. `bootstrap_entity(settings)` copies `harness/template/` into
   `entity/` if `entity/` doesn't exist.
3. `main.py` configures logging to `entity/worker.log` and ensures
   `entity/work/` exists.
4. Two `Entity(settings)` instances are constructed — each builds its
   own `EntityClient` (Anthropic SDK handle) but holds no state yet.
5. `WorkerStatus()` and `threading.Event()` are created.
6. A daemon thread runs `run_worker(...)` unconditionally. Inside the
   worker, `needs_birth()` is checked each tick; if unborn, it idles
   and waits rather than scanning tasks.
7. `run_tui(chat_entity, status, stop_event, settings.tasks_dir)`
   takes the main thread.
8. Inside the TUI, `entity.begin_session()` loads skills, starts a
   transcript, and primes messages with the memory index + recent
   transcripts (or sets up the birth prompt).
9. The TUI draws the banner and opens the live layout.
10. Human types. You respond. Loop.
11. On exit (Ctrl-C / Ctrl-D on empty / `exit`), the TUI sets
    `stop_event`, the worker finishes its current task (or exits on
    its next poll), and `main.py` joins with a 5-second timeout.

## 12. Invariants worth remembering

- **All state is on disk.** Kill the process mid-thought and you lose
  nothing but the current in-memory `messages` list. Your identity,
  memory, notes, skills, and task status are all markdown files.
- **Chat and worker are independent.** They share no `messages`
  history. If you want something from a worker run to influence
  chat, it has to land in a file — a memory, a note, a task update.
- **Skill changes are hot.** Creating, updating, or deleting a skill
  triggers a reload mid-loop; the new tool set is visible on the
  next Claude call in the *same* turn.
- **Identity changes are hot too.** `update_identity` reloads your
  system prompt mid-loop in chat sessions.
- **The worker never runs before birth.** The thread is alive, but
  it sits in an idle-poll loop until `IDENTITY.md` exists — no
  scheduler tick, no task pickup.
- **Tool errors don't crash you.** `registry.execute` catches skill
  exceptions and returns them as `"Error executing skill '<name>': ..."`
  strings in the tool result — you see the failure and can adjust.
- **Web tools are rate-limited per turn.** `max_uses: 10` each for
  `web_search` and `web_fetch`. If you need more, do it across
  turns.
- **Streaming is a chat-only surface.** The underlying call is the
  same streaming API for chat and worker, but the worker passes no
  `on_text` callback, so nothing is rendered incrementally. Don't
  write skills that depend on observing mid-stream state.
- **The transcript is append-only within a session.** It's written
  line-by-line as turns happen, so even a crash mid-response leaves
  a partial record.

---

If something in this file ever drifts from the code in `harness/`,
trust the code and update this file. The harness is the territory;
this document is the map.
