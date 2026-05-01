import logging
import re
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import frontmatter

from harness.entity import Entity
from harness.runtime.status import WorkerStatus


log = logging.getLogger(__name__)

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PLANNING_TASK_TAG = "planning-tick"
PLANNING_TASK_TITLE = "Review responsibilities"
PLANNING_TASK_PRIORITY = "low"
_PENDING_STATUSES = {"todo", "in-progress"}

_INTERVAL_RE = re.compile(r"^\s*(\d+)\s*([smhdw])\s*$", re.IGNORECASE)
_INTERVAL_UNITS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
}


def _parse_interval(value: object) -> timedelta | None:
    """Parse a human review_interval like '30m', '4h', '1d' into a timedelta.
    Returns None if unset or unparseable (caller treats as 'always due')."""
    if value is None or value == "":
        return None
    match = _INTERVAL_RE.match(str(value))
    if not match:
        log.warning("unparseable review_interval %r; treating as always due", value)
        return None
    qty, unit = match.groups()
    return timedelta(seconds=int(qty) * _INTERVAL_UNITS[unit.lower()])


def _parse_iso(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class PendingTask:
    path: Path
    title: str
    priority: str
    created: str


def _next_todo(tasks_dir: Path) -> PendingTask | None:
    if not tasks_dir.exists():
        return None
    candidates: list[PendingTask] = []
    for path in sorted(tasks_dir.glob("*.md")):
        if path.name.startswith("."):
            continue
        try:
            post = frontmatter.load(path)
        except Exception:
            continue
        fm = post.metadata or {}
        if fm.get("status") != "todo":
            continue
        candidates.append(
            PendingTask(
                path=path,
                title=str(fm.get("title", path.stem)),
                priority=str(fm.get("priority", "medium")),
                created=str(fm.get("created", "")),
            )
        )
    if not candidates:
        return None
    candidates.sort(
        key=lambda t: (PRIORITY_ORDER.get(t.priority, 1), t.created, t.path.name)
    )
    return candidates[0]


def _set_status(path: Path, status: str, *, note: str | None = None) -> None:
    """Rewrite a task's frontmatter status. Used only for defensive cleanup
    (before/after the entity's own skill calls) — the entity itself should
    call `update_task`/`complete_task` to transition state during a run."""
    try:
        post = frontmatter.load(path)
        post.metadata["status"] = status
        if note:
            body = post.content.rstrip("\n")
            post.content = body + f"\n\n---\n*Worker note*\n\n{note}\n"
        with path.open("w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
    except Exception as exc:
        log.warning("failed to set status on %s: %s", path, exc)


def _planning_task_pending(tasks_dir: Path) -> bool:
    """True if a planning-tick task is already in the queue (todo or
    in-progress). Dedupes against crash-mid-write and against a still-running
    prior tick."""
    if not tasks_dir.exists():
        return False
    for path in tasks_dir.glob("*.md"):
        if path.name.startswith("."):
            continue
        try:
            post = frontmatter.load(path)
        except Exception:
            continue
        fm = post.metadata or {}
        tags = fm.get("tags") or []
        if PLANNING_TASK_TAG not in tags:
            continue
        if fm.get("status") in _PENDING_STATUSES:
            return True
    return False


@dataclass
class ActiveResponsibility:
    name: str
    description: str
    last_reviewed: str | None
    review_interval: str | None


def active_responsibilities(
    responsibilities_dir: Path,
) -> list[ActiveResponsibility]:
    """Return enabled responsibilities, sorted by last_reviewed ascending
    (None first) so neglected ones surface first. No due-ness filtering."""
    if not responsibilities_dir.exists():
        return []
    entries: list[ActiveResponsibility] = []
    for path in sorted(responsibilities_dir.glob("*.md")):
        if path.name.startswith("."):
            continue
        try:
            post = frontmatter.load(path)
        except Exception:
            log.warning("failed to load responsibility %s", path.name)
            continue
        fm = post.metadata or {}
        if not fm.get("enabled", True):
            continue
        name = str(fm.get("name") or path.stem)
        description = str(fm.get("description") or "")
        last_reviewed_raw = fm.get("last_reviewed")
        last_reviewed = (
            str(last_reviewed_raw) if last_reviewed_raw not in (None, "") else None
        )
        review_interval_raw = fm.get("review_interval")
        review_interval = (
            str(review_interval_raw)
            if review_interval_raw not in (None, "")
            else None
        )
        entries.append(
            ActiveResponsibility(name, description, last_reviewed, review_interval)
        )
    entries.sort(
        key=lambda e: (e.last_reviewed is not None, e.last_reviewed or "", e.name)
    )
    return entries


def _due_responsibilities(
    responsibilities: list[ActiveResponsibility], now: datetime
) -> list[ActiveResponsibility]:
    """Filter to responsibilities whose review_interval has elapsed since
    last_reviewed. Responsibilities without a review_interval are always due."""
    due: list[ActiveResponsibility] = []
    for r in responsibilities:
        interval = _parse_interval(r.review_interval)
        if interval is None:
            due.append(r)
            continue
        last = _parse_iso(r.last_reviewed)
        if last is None or now - last >= interval:
            due.append(r)
    return due


def _planning_task_body(responsibilities: list[ActiveResponsibility]) -> str:
    intro = (
        "The task queue is empty. This is a planning tick — your chance to look "
        "at your standing responsibilities and decide whether any of them want "
        "follow-up work right now.\n\n"
        "**This is a plan-only task.** Your job is NOT to do the work. Your job "
        "is to:\n\n"
        "  1. Read each active responsibility below.\n"
        "  2. For each one, decide: does it want a task right now? Most of the "
        "time the answer is no — that's fine.\n"
        "  3. For the ones that do, call `create_task` with a concrete, "
        "well-scoped plan. The worker will pick those tasks up after this one "
        "completes.\n"
        "  4. Call `update_responsibility` on each one you reviewed (even with "
        "no field changes) so its `last_reviewed` timestamp advances and it "
        "doesn't surface again until its `review_interval` elapses.\n"
        "  5. Call `complete_task` to finish this planning tick.\n\n"
        "Do NOT do the underlying work in this task. If a responsibility wants "
        "something done, that's a `create_task` call, not inline action. "
        "Keeping this task short keeps the worker responsive."
    )

    sections = ["## Responsibilities due for review", ""]
    for r in responsibilities:
        last = r.last_reviewed or "never"
        interval = r.review_interval or "every tick"
        sections.append(
            f"### {r.name}\n"
            f"- description: {r.description}\n"
            f"- last_reviewed: {last}\n"
            f"- review_interval: {interval}"
        )
        sections.append("")

    return f"{intro}\n\n---\n\n" + "\n".join(sections).rstrip() + "\n"


def _enqueue_planning_task(
    tasks_dir: Path, responsibilities: list[ActiveResponsibility], now: datetime
) -> Path:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    body = _planning_task_body(responsibilities)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_review_responsibilities.md"
    filepath = tasks_dir / filename

    fm = {
        "title": PLANNING_TASK_TITLE,
        "created": now.isoformat(),
        "status": "todo",
        "priority": PLANNING_TASK_PRIORITY,
        "tags": [PLANNING_TASK_TAG],
        "author": "harness",
    }
    post = frontmatter.Post(body, **fm)
    filepath.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return filepath


def run_worker(
    entity: Entity,
    status: WorkerStatus,
    stop_event: threading.Event,
    tasks_dir: Path,
    responsibilities_dir: Path,
    poll_interval: float = 10.0,
    planning_cooldown_minutes: float = 1.0,
) -> None:
    """Poll tasks_dir for `status: todo` tasks and work them one at a time.

    When the queue goes empty AND the planning tick interval has elapsed,
    check whether any active responsibilities are due for review (per their
    `review_interval` vs. `last_reviewed`). If at least one is due, enqueue
    a synthetic "Review responsibilities" task listing only those. The
    interval is a floor on tick frequency; per-responsibility intervals
    drive actual cadence. Dedup prevents stacking ticks.

    Runs until stop_event is set. Each task is handed to
    `entity.work_on_task`, which is expected to complete or update it via
    its own skills. If the entity raises, the task is marked blocked.
    """
    log.info("worker starting")
    tick_interval = timedelta(minutes=planning_cooldown_minutes)
    last_planning_tick: datetime | None = None
    waiting_logged = False
    ready_logged = False
    while not stop_event.is_set():
        if entity.needs_birth():
            if not waiting_logged:
                log.info("worker waiting for birth")
                waiting_logged = True
            stop_event.wait(poll_interval)
            continue
        if not ready_logged:
            log.info("worker ready; polling %s every %.1fs", tasks_dir, poll_interval)
            ready_logged = True

        task = _next_todo(tasks_dir)
        if task is None:
            now = datetime.now(timezone.utc)
            tick_elapsed = (
                last_planning_tick is None or now - last_planning_tick >= tick_interval
            )
            if tick_elapsed and not _planning_task_pending(tasks_dir):
                due = _due_responsibilities(
                    active_responsibilities(responsibilities_dir), now
                )
                if due:
                    try:
                        _enqueue_planning_task(tasks_dir, due, now)
                        last_planning_tick = now
                        log.info("planning tick enqueued (%d due)", len(due))
                    except Exception:
                        log.exception("failed to enqueue planning tick")
                else:
                    last_planning_tick = now
            stop_event.wait(poll_interval)
            continue

        # Pre-transition to in-progress so the next poll doesn't re-grab it
        # if the entity forgets to update state mid-run.
        _set_status(task.path, "in-progress")
        status.start_task(task.title, task.path.name)
        log.info("worker picked up task: %s", task.title)

        try:
            entity.work_on_task(
                task.path,
                on_tool_use=status.record_tool,
            )
        except Exception:
            tb = traceback.format_exc()
            log.exception("worker error on task %s", task.path.name)
            # Only rewrite status if the task is still on disk (wasn't
            # completed/archived by the entity mid-run).
            if task.path.exists():
                _set_status(task.path, "blocked", note=f"Worker exception:\n```\n{tb}\n```")
        finally:
            status.finish()

        # Short breath before the next poll to avoid hot-looping if the
        # queue has many ready tasks.
        if stop_event.wait(0.5):
            break

    log.info("worker stopped")
