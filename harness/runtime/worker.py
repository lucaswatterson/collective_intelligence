import logging
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from harness.entity import Entity
from harness.runtime.status import WorkerStatus


log = logging.getLogger(__name__)

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


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


def run_worker(
    entity: Entity,
    status: WorkerStatus,
    stop_event: threading.Event,
    tasks_dir: Path,
    poll_interval: float = 10.0,
) -> None:
    """Poll tasks_dir for `status: todo` tasks and work them one at a time.

    Runs until stop_event is set. Each task is handed to
    `entity.work_on_task`, which is expected to complete or update it via
    its own skills. If the entity raises, the task is marked blocked.
    """
    log.info("worker starting")
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
        else:
            # Task loop finished cleanly but the entity never called
            # complete_task/update_task. Don't leave it silently stuck —
            # mark blocked so it shows up on next triage.
            if task.path.exists():
                try:
                    post = frontmatter.load(task.path)
                    if (post.metadata or {}).get("status") == "in-progress":
                        log.warning(
                            "task %s returned from entity but was not completed or updated",
                            task.path.name,
                        )
                        _set_status(
                            task.path,
                            "blocked",
                            note="Entity finished its turn without calling `complete_task` or `update_task`. Check worker.log for stop_reason.",
                        )
                except Exception:
                    log.exception("failed post-task status check on %s", task.path.name)
        finally:
            status.finish()

        # Short breath before the next poll to avoid hot-looping if the
        # queue has many ready tasks.
        if stop_event.wait(0.5):
            break

    log.info("worker stopped")
