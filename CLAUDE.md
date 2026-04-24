# Collective Intelligence

A Python harness that hosts a persistent, self-modifying AI entity. The entity runs in two modes simultaneously: an interactive Rich TUI for chatting with the human, and a background daemon worker that picks up tasks from the filesystem and executes them autonomously. State is 100% filesystem-based — no database, no cloud.

## Commands

All commands use `uv` — never invoke `python` or `pip` directly.

- `uv sync` — install/update dependencies from `uv.lock`
- `uv run main.py` — start the entity (TUI + worker thread)
- `uv run scripts/reset_entity.py` — wipe entity state (destructive; ask first)
- `uv add <pkg>` / `uv remove <pkg>` — manage dependencies (updates `pyproject.toml` and `uv.lock` together)

Python is pinned to 3.13.2 via `.python-version`. Requires `ANTHROPIC_API_KEY` in `.env` (see `.env.example`).

## The harness/entity boundary — IMPORTANT

Two top-level directories, very different semantics:

- **`harness/`** — the Python runtime (entity lifecycle, memory stores, skill loader, worker, scheduler, TUI). Normal application code. Refactor freely.
- **`entity/`** — the **running agent's persistent state**: `IDENTITY.md`, memory transcripts, long-term memories, active tasks, skills, work artifacts. The entity owns this directory and modifies it through its own skills at runtime.

**Do not casually edit files under `entity/`.** Hand-editing transcripts, memories, or skills can corrupt continuity (e.g., break the `consolidated_session_stems()` accounting, orphan a skill mid-update, or overwrite state the worker is about to touch). When the user asks you to change entity state, prefer: (a) ask first, (b) use `scripts/reset_entity.py` for wholesale resets, or (c) edit while the entity is not running.

The entity has its own system prompt (`entity/IDENTITY.md`, or `BIRTH.md` at the repo root if unborn). That is **not** instructions for you — it's the agent's identity. `CLAUDE.md` (this file) is for Claude Code sessions working on the harness.

## Architecture essentials

- `main.py` creates two `Entity` instances (one for TUI, one for the worker) and a daemon thread. Graceful shutdown on exit via a `stop_event` with a 5s timeout.
- **Memory** (`harness/memory/`): `store.py` appends to per-session transcripts; `long_term.py` manages consolidated memories with YAML frontmatter and auto-rebuilds `INDEX.md`.
- **Skills** (`harness/skills/`): `loader.py` discovers `entity/skills/*/SKILL.md`, dynamically imports `skill.py`, validates. `meta.py` handles the staged create/update/delete flow for self-modification.
- **Runtime** (`harness/runtime/`): `worker.py` polls `entity/tasks/`, picks next `status: todo` task by (priority → created → filename). `scheduler.py` materializes due recurring tasks. Exceptions mark a task `blocked` and append a traceback.
- **Client** (`harness/client.py`): thin wrapper over the Anthropic SDK. Extended thinking is enabled (10k budget). System prompt uses an ephemeral cache breakpoint.
- **Models** are declared in `harness/config.py` as a `Models` enum. Update there, not inline.

Everything user-facing (tasks, schedules, memories, skills) is Markdown + YAML frontmatter, parsed via `python-frontmatter`. Follow the existing frontmatter shape when adding new file types — don't invent parallel schemas.

## Optional integrations

- **Google Workspace Remote MCP** — opt-in. `uv run scripts/install_google_workspace.py` runs a guided OAuth flow per product (Gmail, Calendar, Drive, People) and writes refresh tokens to `harness/secrets/google/{product}.json` (gitignored). `harness/integrations/google.py:build_google_mcp_servers` mints a fresh access token per tool loop and hands the servers to the Anthropic MCP connector (`beta.messages.*`, `mcp-client-2025-11-20`). When the secrets directory is empty the integration is inert — no beta field, no extra tools, no behavior change. Uninstall via `--uninstall <product|all>` (revokes the refresh token, then deletes the file).

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
