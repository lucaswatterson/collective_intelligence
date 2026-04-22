import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import frontmatter


log = logging.getLogger(__name__)

_INTERVAL_RE = re.compile(r"^(\d+)([smhd])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_PENDING_STATUSES = {"todo", "in-progress", "blocked"}
_SLUG_RE = re.compile(r"[^a-z0-9]+")


def parse_interval(s: str) -> timedelta:
    if not isinstance(s, str):
        raise ValueError(f"interval must be a string, got {type(s).__name__}")
    m = _INTERVAL_RE.match(s.strip())
    if not m:
        raise ValueError(
            f"invalid interval {s!r}; expected e.g. '30s', '15m', '1h', '2d'"
        )
    n, unit = int(m.group(1)), m.group(2)
    if n <= 0:
        raise ValueError(f"interval must be positive, got {s!r}")
    return timedelta(seconds=n * _UNIT_SECONDS[unit])


def _parse_last_run(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        dt = datetime.fromisoformat(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise ValueError(f"unrecognized last_run value: {value!r}")


def _has_pending_for(tasks_dir: Path, schedule_name: str) -> bool:
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
        if fm.get("schedule") != schedule_name:
            continue
        if fm.get("status") in _PENDING_STATUSES:
            return True
    return False


def _slug(s: str) -> str:
    return _SLUG_RE.sub("_", s.lower()).strip("_")[:50]


def _write_task(tasks_dir: Path, schedule_name: str, fm: dict, body: str, now: datetime) -> Path:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    title = str(fm.get("task_title") or schedule_name)
    filename = f"{timestamp}_{_slug(schedule_name)}.md"
    filepath = tasks_dir / filename

    task_fm = {
        "title": title,
        "created": now.isoformat(),
        "status": "todo",
        "priority": fm.get("task_priority", "medium"),
        "tags": list(fm.get("task_tags") or []),
        "author": fm.get("author", "agent"),
        "schedule": schedule_name,
    }
    post = frontmatter.Post(body, **task_fm)
    filepath.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return filepath


def _update_last_run(schedule_path: Path, now: datetime) -> None:
    post = frontmatter.load(schedule_path)
    post.metadata["last_run"] = now.isoformat()
    schedule_path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


def materialize_due_schedules(
    schedules_dir: Path, tasks_dir: Path, now: datetime
) -> list[str]:
    """For each enabled schedule whose next_fire <= now, if no pending task
    with a matching `schedule:` field exists, materialize a new task and
    update last_run. Returns names of schedules that fired.
    """
    if not schedules_dir.exists():
        return []

    fired: list[str] = []
    for path in sorted(schedules_dir.glob("*.md")):
        if path.name.startswith("."):
            continue
        try:
            post = frontmatter.load(path)
        except Exception:
            log.exception("failed to load schedule %s", path.name)
            continue
        fm = post.metadata or {}

        if not fm.get("enabled", True):
            continue

        name = str(fm.get("name") or path.stem)
        try:
            interval = parse_interval(str(fm.get("interval", "")))
        except ValueError:
            log.exception("bad interval on schedule %s", path.name)
            continue

        try:
            last_run = _parse_last_run(fm.get("last_run"))
        except ValueError:
            log.exception("bad last_run on schedule %s", path.name)
            continue

        next_fire = now if last_run is None else last_run + interval
        if next_fire > now:
            continue

        if _has_pending_for(tasks_dir, name):
            log.info("scheduler skipping %s: pending task exists", name)
            continue

        try:
            _write_task(tasks_dir, name, fm, post.content, now)
            _update_last_run(path, now)
            fired.append(name)
        except Exception:
            log.exception("failed to materialize schedule %s", name)

    return fired
