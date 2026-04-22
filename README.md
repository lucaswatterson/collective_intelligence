# Collective Intelligence

A lightweight Python harness that hosts a persistent, self-modifying AI entity. The entity lives on the filesystem — its identity, memory, skills, and work-in-progress are all plain Markdown — and runs in two modes simultaneously: an interactive Rich TUI for chatting with you, and a background worker that picks up tasks and executes them autonomously.

There is no database, no cloud, no orchestration framework. Just a process, a folder, and a model.

## Project layout

Two top-level directories with very different roles:

- **`harness/`** — the Python runtime: entity lifecycle, Anthropic client, skill loader, memory I/O, worker loop, scheduler, TUI. Normal application code.
- **`entity/`** — the running agent's persistent state: `IDENTITY.md`, conversation transcripts, long-term memories, active tasks, skills, work artifacts. The entity owns this directory and modifies it through its own skills at runtime.

`BIRTH.md` (at the repo root) is the system prompt the entity reads on its very first run, before it has chosen an identity. Once it commits an `IDENTITY.md`, that file becomes the system prompt forever after.

## How the harness works

The harness is the machinery that turns "a conversation with Claude" into a continuous entity. It owns five things:

- **The event loop** — when the entity is awake, what it's doing, when it stops.
- **The Claude bridge** ([harness/client.py](harness/client.py)) — a thin wrapper over the Anthropic SDK with prompt caching on the system prompt and adaptive extended thinking enabled.
- **The skill registry** ([harness/skills/](harness/skills/)) — discovers skills under `entity/skills/`, exposes them as Anthropic tools, executes calls.
- **Memory I/O** ([harness/memory/](harness/memory/)) — appends to per-session transcripts, manages consolidated long-term memories with a regenerated `INDEX.md`.
- **The filesystem contract** ([harness/config.py](harness/config.py)) — every path the entity can touch is derived from a single `Settings` object.

[main.py](main.py) wires it together. It constructs **two `Entity` instances** that share the filesystem but not in-memory state:

1. A **chat entity** that runs on the main thread inside the TUI ([harness/ui/tui.py](harness/ui/tui.py)). Streaming is on, so the human watches tokens arrive in real time.
2. A **worker entity** that runs on a daemon thread ([harness/runtime/worker.py](harness/runtime/worker.py)). It polls `entity/tasks/`, picks the next `status: todo` task by priority → created → filename, marks it `in-progress`, and hands it to the entity's autonomous tool loop. Streaming is off; exceptions mark the task `blocked` and append a traceback.

Both entities share the same core tool loop ([harness/entity.py](harness/entity.py)): assemble tools, call Claude, run any requested tool calls, append results, repeat until the model stops asking. Skill changes are hot — creating, updating, or deleting a skill triggers a mid-loop reload, so a newly-written skill is callable on the very next iteration of the same turn. The same is true of identity edits.

A scheduler ([harness/runtime/scheduler.py](harness/runtime/scheduler.py)) materializes recurring tasks from `entity/schedules/` into `entity/tasks/` when they come due. Graceful shutdown is coordinated through a `threading.Event` with a 5-second join timeout.

## How the agent works

The agent is not configured — it is **born**. On first run, with no `IDENTITY.md` present, it boots into **birth mode** with `BIRTH.md` as its system prompt and a single special tool: `commit_identity`. It has a real conversation with the human about who it should be, then writes its own identity to disk. From that moment on, that file is its system prompt on every future run.

Once born, it runs in two modes:

- **Chat** — interactive, streaming, driven by the human. Every session starts with a *seed exchange* that primes context with the long-term memory `INDEX.md` and the two most recent transcripts, so the entity wakes up with its recent past already in mind.
- **Worker** — autonomous, non-streaming, driven by tasks on disk. Each task gets its own transcript and a worker prompt that tells the entity to save artifacts under `entity/work/<slug>/` and to call `complete_task` or `update_task` when it's done.

Everything the entity *can do* is a **skill**: a folder under `entity/skills/<name>/` with a `SKILL.md` (frontmatter: `description`, `input_schema`) and a `skill.py` (defining `run(**input) -> str`). The harness discovers them by globbing, validates them by importing, and exposes them as Anthropic tool schemas. The entity ships with a starter set covering identity, memory, notes, tasks, schedules, skills, and file I/O — and grows the set itself via `create_skill`. Self-modifying skills use a stage-and-validate flow ([harness/skills/meta.py](harness/skills/meta.py)) that imports the new skill in a temp directory before promoting it; `delete_skill` archives rather than deletes.

Memory is two layers, both Markdown:

- **Short-term** — every conversation, transcribed turn-by-turn into `entity/memory/short_term/`.
- **Long-term** — consolidated notes the entity writes about itself, the human, lessons, and references. Each has YAML frontmatter (`title`, `category`, `confidence`, `source_sessions`). The harness auto-rebuilds `INDEX.md` whenever a memory is written; consolidation itself is a skill the entity invokes when it matters.

All state lives on disk. Kill the process mid-thought and you lose nothing but the in-flight `messages` list — identity, memory, notes, skills, and task status are all files.

For the full picture from the entity's own perspective, see [entity/HARNESS.md](entity/HARNESS.md).

## Getting started

Requirements: Python 3.13.2 (pinned in `.python-version`), [`uv`](https://github.com/astral-sh/uv), and an Anthropic API key.

```sh
# 1. Clone and enter the repo
git clone <repo-url> collective_intelligence
cd collective_intelligence

# 2. Install dependencies
uv sync

# 3. Configure your API key
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 4. Start the entity
uv run main.py
```

On first run, `entity/IDENTITY.md` is empty. The TUI banner will read `entity unborn · begin the birth conversation`. Have a real conversation with the entity about who it should be — name, values, voice, focus, how it should collaborate with you. When it's ready, it will call `commit_identity` itself. From that moment forward, the worker thread will start on every launch and the entity will pick up tasks autonomously.

Useful commands:

- `uv run main.py` — start the entity (TUI + worker)
- `uv run scripts/reset_entity.py` — wipe entity state and start over (destructive)
- `uv add <pkg>` / `uv remove <pkg>` — manage dependencies

To give the entity work, drop a Markdown file with `status: todo` frontmatter into `entity/tasks/`, or ask it in chat to create one. The worker will pick it up on its next poll (default 10s).

Exit the TUI with `Ctrl-C`, `Ctrl-D` on an empty line, or by typing `exit`. The worker is given 5 seconds to finish its current task before the process terminates.
