# Collective Intelligence

A Python harness that hosts a persistent, self-modifying AI entity. The entity runs in two modes: an interactive Rich TUI for chatting with the human, and a background worker that picks up tasks from the filesystem and executes them autonomously. The two can run together in one process, or the worker can run headless and the TUI can attach to it later. State is 100% filesystem-based — no database, no cloud.

## Commands

All commands use `uv` — never invoke `python` or `pip` directly.

- `uv sync` — install/update dependencies from `uv.lock`
- `uv run ci tui` — start the entity. Auto-detects via `entity/worker.pid`: if no worker is running, spawns TUI + worker thread; if one is already running, just attaches a TUI.
- `uv run ci worker start` — launch the worker as a detached background process. Returns immediately; logs go to `entity/worker.log`. Refuses if another worker is already running.
- `uv run ci worker stop` — `SIGTERM` the running worker and wait up to 10 s for it to exit.
- `uv run ci worker status` — print whether a worker is running, its PID, and its current activity (from `entity/worker_status.json`).
- `uv run scripts/reset_entity.py` — wipe entity state (destructive; ask first)
- `uv add <pkg>` / `uv remove <pkg>` — manage dependencies (updates `pyproject.toml` and `uv.lock` together)

Python is pinned to 3.13.2 via `.python-version`. Requires `ANTHROPIC_API_KEY` in `.env` (see `.env.example`).

## The harness/entity boundary — IMPORTANT

Two top-level directories, very different semantics:

- **`harness/`** — the Python runtime (entity lifecycle, memory stores, skill loader, worker, TUI). Normal application code. Refactor freely.
- **`entity/`** — the **running agent's persistent state**: `IDENTITY.md`, memory transcripts, long-term memories, active tasks, skills, work artifacts. The entity owns this directory and modifies it through its own skills at runtime.

**Do not casually edit files under `entity/`.** Hand-editing transcripts, memories, or skills can corrupt continuity (e.g., break the `consolidated_session_stems()` accounting, orphan a skill mid-update, or overwrite state the worker is about to touch). When the user asks you to change entity state, prefer: (a) ask first, (b) use `scripts/reset_entity.py` for wholesale resets, or (c) edit while the entity is not running.

The entity has its own system prompt (`entity/IDENTITY.md`, or `BIRTH.md` at the repo root if unborn). That is **not** instructions for you — it's the agent's identity. `CLAUDE.md` (this file) is for Claude Code sessions working on the harness.

## Architecture essentials

- `harness/cli.py` is the entry point for the `ci` console script. It exposes three runtime modes via subcommands: combined (`ci tui` when no worker is running — TUI + worker thread), headless (`ci worker start` spawns a detached child whose `_run` subcommand runs the worker on the main thread with `SIGINT`/`SIGTERM` handlers), and TUI-only (`ci tui` when a worker is already running — attaches via `FileBackedWorkerStatus`). Mode for `ci tui` is decided by checking `entity/worker.pid`. Combined mode creates two `Entity` instances and a daemon thread; graceful shutdown via a `stop_event` with a 5 s timeout. TUI-only mode does not signal the external worker on exit. `ci worker start` itself just `Popen`s the child with `start_new_session=True` and polls for the PID file before returning.
- **Cross-process status** (`harness/runtime/status.py`): `WorkerStatus` writes a JSON snapshot to `entity/worker_status.json` on every state change so a TUI in another process can read it. `FileBackedWorkerStatus(path)` is the read-only adapter the attached TUI uses; both expose the same `.snapshot()` API.
- **PID file** (`harness/runtime/lifecycle.py`): the worker writes its PID to `entity/worker.pid` on start and removes it on clean shutdown. `worker_already_running()` returns the PID if alive (via `os.kill(pid, 0)`); a stale file is ignored and overwritten.
- **Memory** (`harness/memory/`): `store.py` appends to per-session transcripts; `long_term.py` manages consolidated memories with YAML frontmatter and auto-rebuilds `INDEX.md`.
- **Skills** (`harness/skills/`): `loader.py` discovers `entity/skills/*/SKILL.md`, dynamically imports `skill.py`, validates. `meta.py` handles the staged create/update/delete flow for self-modification.
- **Runtime** (`harness/runtime/`): `worker.py` polls `entity/tasks/`, picks next `status: todo` task by (priority → created → filename). Each cycle it also runs a *schedule pass*: `schedule.py` reads `entity/SCHEDULE.md`, and for any entry whose `interval` or `cron` cadence is due (relative to `last_run`), the worker reads the referenced responsibility, inlines its body into a fresh task, and snaps `last_run` to now. Catch-up is fire-once — a long offline period produces one task per overdue entry, not a flood. Exceptions mark a task `blocked` and append a traceback.
- **Client** (`harness/client.py`): thin wrapper over the Anthropic SDK. Extended thinking is enabled (10k budget). System prompt uses an ephemeral cache breakpoint.
- **Models** are declared in `harness/config.py` as a `Models` enum. Update there, not inline.

Everything user-facing (tasks, responsibilities, memories, skills) is Markdown + YAML frontmatter, parsed via `python-frontmatter`. Follow the existing frontmatter shape when adding new file types — don't invent parallel schemas.

## Conventions

- Modern Python 3.13: native generics (`list[T]`, `dict[K, V]`), no `from __future__ import annotations`.
- Paths are `pathlib.Path`, never strings.
- Logging goes through the `logging` module; the worker writes to `entity/worker.log`.
- No test suite, no linter config, no type-check config — don't fabricate one unless asked. Type hints are present but not enforced.

## Gotchas

- **Skills aren't deleted, they're archived.** `delete_skill` moves to `entity/skills/.archive/<timestamp>/`. If you're looking for "missing" skill code, check there.
- **Two entities, one process.** The TUI entity and the worker entity share the filesystem but not memory state. Don't assume in-memory invariants across them.
- **Self-modifying skills stage before committing.** `meta.stage_and_validate()` writes to a temp dir and import-checks before `commit_staged_skill()` moves it into place. Preserve this pattern for any new meta-skill work.
- **The TUI uses raw TTY mode.** Running it inside another TUI or a non-tty context will break input handling.
- **Schedule mutates on every fire.** The schedule pass updates `last_run` in place and rewrites `SCHEDULE.md` once per pass. Don't hand-edit while the worker is running unless you're OK losing the change to a concurrent write.
- **Responsibilities and schedule are decoupled.** Responsibilities (`entity/responsibilities/<name>.md`) hold the contract — *what* to do. The schedule (`entity/SCHEDULE.md`) holds *when* — interval or cron — and references responsibilities by stem. Creating a responsibility doesn't make it run; you also need a schedule entry (via `manage_schedule`).
