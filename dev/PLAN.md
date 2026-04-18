# Collective Intelligence — High-Level Project Plan

## Context

Collective Intelligence is a lightweight harness for an autonomous AI entity. The entity owns the `entity/` folder (its files, memory, skills, public site). On startup it consults `IDENTITY.md`; if empty, it bootstraps itself from `BIRTH.md`. Long-term it runs as an always-on process with cron-triggered memory consolidation and scheduled skill execution, eventually inside a container with a clean web representation.

This plan establishes the architecture and a phased build order. The current repo is scaffolding only (empty `IDENTITY.md`, empty `BIRTH.md`, empty `entity/{files,memory,public,skills}` directories, a stub `main.py`, and `anthropic` as the only dependency).

## Design decisions (locked in)

- **Autonomy**: always-on loop with cron triggers (wakes on schedule/events, acts without user prompting).
- **Entity model**: single persistent entity. Parallel work is delegated to ephemeral sub-agents invoked as tools (Anthropic SDK).
- **Skills**: Anthropic Skills format — each skill is a folder under `entity/skills/<name>/` with a `SKILL.md` (frontmatter: `name`, `description`, when-to-use) and optional scripts/resources. Loaded on demand.
- **Birth**: `BIRTH.md` is a bootstrap system prompt. On first run, the entity reads it, has a "birth" conversation, and writes its own `IDENTITY.md`. Identity is emergent.
- **Memory**: file-based, markdown with frontmatter. `entity/memory/short_term/` for raw session transcripts; `entity/memory/long_term/` for consolidated, indexed notes (organized semantically). Cron jobs consolidate short → long.
- **Terminal UX**: Rich TUI (Textual). Panels for conversation, memory state, active skills, scheduled jobs.
- **Phasing**: foundation first; loop/integrations/web/container land later.
- **SDK & models**: Anthropic Python SDK, latest Claude models (Opus 4.7 for reasoning-heavy work, Sonnet 4.6 / Haiku 4.5 for routine and fast paths). Centralize model selection in config.

## Target architecture

```
collective_intelligence/
├── entity/                   # Entity-owned (persists across runs, mounted as volume in container)
│   ├── IDENTITY.md           # Written by entity on first birth
│   ├── files/                # Knowledge, generated artifacts
│   ├── memory/
│   │   ├── short_term/       # Session transcripts (raw)
│   │   └── long_term/        # Consolidated, indexed memories (semantic folders)
│   ├── public/               # Static site representing the entity
│   └── skills/               # <name>/SKILL.md + scripts/
│       └── <skill_name>/SKILL.md
├── BIRTH.md                  # Bootstrap prompt (repo-owned, not entity-owned)
├── src/collective/           # Harness code (entity-agnostic)
│   ├── config.py             # Env, paths, model selection
│   ├── entity.py             # Entity lifecycle: birth check, identity load, run loop
│   ├── client.py             # Anthropic SDK wrapper (streaming, prompt caching, sub-agents)
│   ├── skills/
│   │   ├── loader.py         # Discover entity/skills/*, parse SKILL.md frontmatter
│   │   └── registry.py       # Match user/entity intent → skill
│   ├── memory/
│   │   ├── store.py          # Read/write markdown with frontmatter
│   │   ├── recall.py         # Pull relevant memories into context
│   │   └── consolidate.py    # short_term → long_term summarization (cron-driven)
│   ├── scheduler/
│   │   ├── cron.py           # APScheduler (or similar) for periodic jobs
│   │   └── jobs.py           # Memory consolidation, scheduled skill runs
│   └── ui/
│       ├── tui.py            # Textual app (later phase)
│       └── repl.py           # Plain REPL (phase 1 stopgap)
└── main.py                   # Entry point: parse args, init entity, dispatch to UI/loop
```

## Phased build order

### Phase 1 — Foundation (terminal-only, no autonomy)
Goal: an entity that can be born, remember a conversation, and use one trivial skill from a REPL.

- **Config** (`src/collective/config.py`): load `.env`, define paths, expose model IDs.
- **Anthropic client wrapper** (`client.py`): streaming responses, prompt caching on the IDENTITY/BIRTH system prompt, helper for sub-agent spawning.
- **Birth flow** (`entity.py`):
  - On startup, read `entity/IDENTITY.md`. If empty, load `BIRTH.md` as system prompt and start a birth conversation in the REPL. The entity writes its own `IDENTITY.md` when ready.
  - On subsequent runs, load `IDENTITY.md` as the system prompt.
- **Skill loader** (`skills/loader.py`, `skills/registry.py`): scan `entity/skills/*/SKILL.md`, parse frontmatter, expose to the model as discoverable capabilities. Load skill bodies on demand.
- **Memory v0** (`memory/store.py`): append session transcript to `entity/memory/short_term/<timestamp>.md`. Read recent transcripts back into context on startup.
- **REPL** (`ui/repl.py`): plain stdin/stdout loop, streamed responses. This is a stopgap — Textual TUI in Phase 4.
- **One sample skill**: e.g. `entity/skills/note/SKILL.md` that writes to `entity/files/`.
- **`BIRTH.md` content**: write the actual bootstrap prompt (entity priors, values, instructions for self-authoring `IDENTITY.md`).

Deliverable: `uv run main.py` walks through birth on first run, then opens a REPL where the entity remembers prior sessions.

### Phase 2 — Always-on loop & memory consolidation
Goal: entity runs continuously and tends its own memory.

- **Scheduler** (`scheduler/cron.py`): adopt APScheduler. Define jobs in `scheduler/jobs.py`.
- **Memory consolidation** (`memory/consolidate.py`): nightly job summarizes `short_term/` into `long_term/`, organized by topic. Uses Haiku for cheap passes.
- **Recall** (`memory/recall.py`): on each turn, surface relevant long-term memories into context (keyword/path-based first; embeddings later if needed).
- **Background "thinking"**: scheduled jobs can invoke the entity to reflect, plan, or act without a user prompt. Output goes to `short_term/` and surfaces in the UI on next attach.
- **Process model**: long-running daemon. REPL/TUI attaches to it (or runs in-process for v1 simplicity).

Deliverable: leave the entity running overnight; next morning, `long_term/` has consolidated notes and the entity references them naturally.

### Phase 3 — External integrations
Goal: entity can act on the outside world via skills.

- **Google Workspace skill** (`entity/skills/google_workspace/`): OAuth setup, Calendar/Gmail/Drive read+write helpers. Credentials live outside `entity/` (in `.env` or a `secrets/` dir).
- **GitHub skill** (`entity/skills/github/`): repo read, issue/PR read+write via `gh` or PyGithub.
- **Skill template + docs**: pattern for adding new integrations (auth, error handling, rate limiting).

Deliverable: entity can read the user's calendar, file an issue, etc., from the REPL or via a scheduled job.

### Phase 4 — Rich TUI + web UI
Goal: real interfaces.

- **Textual TUI** (`ui/tui.py`): panels for conversation, memory state (short/long), active skills, scheduled jobs, recent autonomous actions.
- **Public site** (`entity/public/`): static HTML/CSS, regenerated by the entity (a skill it owns). Visual representation primary; chat secondary. Served by a minimal FastAPI app in `src/collective/web/`.
- **Web chat (secondary)**: same conversation API the TUI uses, exposed over HTTP/WebSocket.

Deliverable: `uv run ci tui` opens the Textual app; `uv run ci serve` serves the public site + chat.

### Phase 5 — Containerization
Goal: portable, reproducible deployment.

- **Dockerfile**: Python 3.13, uv, app code.
- **Volume layout**: `entity/` mounted as a persistent volume so identity/memory/files survive container restarts.
- **Compose file**: app + (later) any sidecars (vector DB if/when adopted).
- **Secrets**: env-injected; document the required vars.

Deliverable: `docker compose up` runs the entity with persistent state.

## Critical files to create/modify (Phase 1 scope)

- Modify: `pyproject.toml` — add `textual` (later), `apscheduler` (Phase 2), `python-dotenv`, `pydantic` (config), `python-frontmatter` (memory/skills parsing).
- Create: `src/collective/{__init__.py, config.py, entity.py, client.py}`
- Create: `src/collective/skills/{__init__.py, loader.py, registry.py}`
- Create: `src/collective/memory/{__init__.py, store.py}`
- Create: `src/collective/ui/repl.py`
- Modify: `main.py` — wire entry point to `entity.run()`.
- Write: `BIRTH.md` — bootstrap prompt.
- Create: `entity/skills/note/SKILL.md` — sample skill.

## Reuse / conventions to follow

- **Anthropic Skills format**: model `SKILL.md` after the conventions used in Claude Code skills (frontmatter with `name`, `description`, when-to-use guidance; body describes how to perform the skill; optional bundled scripts).
- **Memory frontmatter**: model after Claude Code's auto-memory format (`name`, `description`, `type`) so the entity can reason about its memory the same way Claude Code does.
- **Prompt caching**: cache `IDENTITY.md` (and large skill bodies when loaded) as system-prompt cache breakpoints to keep per-turn cost low — important once the always-on loop is firing frequently.
- **Model tiering**: Opus 4.7 for reasoning/decision turns; Sonnet 4.6 default; Haiku 4.5 for memory consolidation, summarization, and routine cron jobs.

## Verification

Per-phase smoke tests rather than a full test suite up front (greenfield, exploratory).

- **Phase 1**: delete `entity/IDENTITY.md`, run `uv run main.py`, complete birth, verify `IDENTITY.md` populated. Restart, verify entity recalls prior conversation. Invoke the sample `note` skill, verify a file appears in `entity/files/`.
- **Phase 2**: run for an extended period; trigger consolidation job manually; verify `long_term/` notes are sensible and that the entity surfaces them in a fresh session.
- **Phase 3**: each integration skill exercised end-to-end (real calendar read, real GitHub issue created on a sandbox repo).
- **Phase 4**: open TUI, confirm panels reflect real state; load public site in a browser.
- **Phase 5**: `docker compose up`, kill the container, restart, verify identity/memory persisted.

## Open questions to revisit (not blocking Phase 1)

- Sub-agent spawning: how the single entity delegates to ephemeral sub-agents — define the tool contract in Phase 2 once memory/skill flows are concrete.
- Embeddings/vector recall: defer until file-based recall proves insufficient.
- Multi-entity future: current layout supports adding `entities/<name>/` later without restructuring; revisit only when a concrete second entity is wanted.
