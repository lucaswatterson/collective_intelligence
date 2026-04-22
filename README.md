# Collective Intelligence

A lightweight Python harness that hosts a persistent, self-modifying AI entity. The entity lives on the filesystem — its identity, memory, skills, and work-in-progress are all plain Markdown — and runs in two modes simultaneously: an interactive Rich TUI for chatting with you, and a background worker that picks up tasks and executes them autonomously.

There is no database, no cloud, no orchestration framework. Just a process, a folder, and a model.

Built on the [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude is the only supported model provider today.

## Quickstart

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

On first launch, the harness bootstraps an `entity/` directory from [harness/template/](harness/template/) — identity, skills, and memory scaffolding. `entity/IDENTITY.md` starts empty and the TUI banner reads `entity unborn · begin the birth conversation`. Have a real conversation with the entity about who it should be — name, values, voice, focus, how it should collaborate with you. When it's ready, it calls `commit_identity` itself. From that moment on, the worker thread will start on every launch and the entity will pick up tasks autonomously.

Useful commands:

- `uv run main.py` — start the entity (TUI + worker)
- `uv run scripts/reset_entity.py` — wipe entity state and start over (destructive)
- `uv add <pkg>` / `uv remove <pkg>` — manage dependencies

To give the entity work, drop a Markdown file with `status: todo` frontmatter into `entity/tasks/`, or ask it in chat to create one. The worker picks it up on its next poll (default 10s, configurable via `WORKER_POLL_INTERVAL` — see [harness/config.py:24](harness/config.py:24)).

Exit the TUI with `Ctrl-C`, `Ctrl-D` on an empty line, or by typing `exit`. The worker is given 5 seconds to finish its current task before the process terminates ([main.py:49](main.py:49)).

## How does Collective Intelligence work?

### The harness/entity boundary

Two top-level directories with very different roles:

- **[harness/](harness/)** — the Python runtime: entity lifecycle, Anthropic client, skill loader, memory I/O, worker loop, scheduler, TUI. Normal application code. Also contains [harness/template/](harness/template/), the seed scaffolding copied into `entity/` on first launch.
- **`entity/`** — the running agent's persistent state, created on first launch: `IDENTITY.md`, conversation transcripts, long-term memories, notes, active tasks, recurring schedules, skills, and work artifacts. The entity owns this directory and modifies it through its own skills at runtime.

[harness/BIRTH.md](harness/BIRTH.md) is the system prompt the entity reads on its very first run, before it has chosen an identity. Once it commits an `IDENTITY.md`, that file becomes the system prompt forever after.

### The runtime

[main.py](main.py) wires everything together. It constructs **two `Entity` instances** that share the filesystem but not in-memory state:

1. A **chat entity** that runs on the main thread inside the TUI ([harness/ui/tui.py](harness/ui/tui.py)). Streaming is on, so the human watches tokens arrive in real time.
2. A **worker entity** that runs on a daemon thread ([harness/runtime/worker.py](harness/runtime/worker.py)). It polls `entity/tasks/`, picks the next `status: todo` task by priority → created → filename, marks it `in-progress`, and hands it to the entity's autonomous tool loop. Streaming is off; exceptions mark the task `blocked` and append a traceback.

Both entities share the same core tool loop ([harness/entity.py](harness/entity.py)): assemble tools, call Claude, run any requested tool calls, append results, repeat until the model stops asking. Skill changes are hot — creating, updating, or deleting a skill triggers a mid-loop reload, so a newly-written skill is callable on the very next iteration of the same turn. The same is true of identity edits.

A scheduler ([harness/runtime/scheduler.py](harness/runtime/scheduler.py)) materializes recurring tasks from `entity/schedules/` into `entity/tasks/` when they come due. The Claude bridge ([harness/client.py](harness/client.py)) is a thin wrapper over the Anthropic SDK with prompt caching on the system prompt and extended thinking enabled. Graceful shutdown is coordinated through a `threading.Event` with a 5-second join timeout.

### Birth and identity

The agent is not configured — it is **born**. On first run, with no `IDENTITY.md` present, it boots into **birth mode** using [harness/BIRTH.md](harness/BIRTH.md) as its system prompt and a single special tool: `commit_identity`. It has a real conversation with the human about who it should be, then writes its own identity to disk. From that moment on, that file is its system prompt on every future run.

Once born, it runs in two modes:

- **Chat** — interactive, streaming, driven by the human. Every session starts with a *seed exchange* that primes context with the long-term memory `INDEX.md` and the two most recent transcripts, so the entity wakes up with its recent past already in mind.
- **Worker** — autonomous, non-streaming, driven by tasks on disk. Each task gets its own transcript and a worker prompt that tells the entity to save artifacts under `entity/work/<slug>/` and to call `complete_task` or `update_task` when it's done.

### Skills

Everything the entity *can do* is a **skill**: a folder under `entity/skills/<name>/` with a `SKILL.md` (frontmatter: `description`, `input_schema`) and a `skill.py` (defining `run(**input) -> str`). The harness discovers them by globbing, validates them by importing, and exposes them as Anthropic tool schemas.

The starter set ships in [harness/template/skills/](harness/template/skills/) and is copied into `entity/skills/` on first launch — covering identity, memory, notes, tasks, schedules, skills, and file I/O. The entity grows the set itself via `create_skill`. Self-modifying skills use a stage-and-validate flow ([harness/skills/meta.py](harness/skills/meta.py)) that imports the new skill in a temp directory before promoting it; `delete_skill` archives to `entity/skills/.archive/<timestamp>/` rather than deleting.

### Memory

Two layers, both Markdown:

- **Short-term** — every conversation, transcribed turn-by-turn into `entity/memory/short_term/`.
- **Long-term** — consolidated notes the entity writes about itself, the human, lessons, and references. Each has YAML frontmatter (`title`, `category`, `confidence`, `source_sessions`). The harness auto-rebuilds `INDEX.md` whenever a memory is written; consolidation itself is a skill the entity invokes when it matters.

All state lives on disk. Kill the process mid-thought and you lose nothing but the in-flight `messages` list — identity, memory, notes, skills, and task status are all files.

For the full picture from the entity's own perspective, see `entity/HARNESS.md` (scaffolded on first launch from [harness/template/HARNESS.md](harness/template/HARNESS.md)).
