"""Single-file schedule that drives the worker.

`entity/SCHEDULE.md` lists scheduled entries. Each entry references a
responsibility by stem; when due, the worker reads that responsibility and
inlines its body into a concrete task in `entity/tasks/`. There is no planning
round-trip — the schedule says when, the responsibility says what.

Catch-up policy is *fire once*: if many cron firings or interval periods
elapsed while the worker was off, exactly one task is enqueued and `last_run`
snaps forward to `now`.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any

import frontmatter
from apscheduler.triggers.cron import CronTrigger


log = logging.getLogger(__name__)


def _translate_crontab_dow(field: str) -> str:
    """Translate the day-of-week field from standard crontab convention
    (0=Sun, 1=Mon, ..., 6=Sat, 7=Sun) to APScheduler's internal convention
    (0=Mon, ..., 6=Sun). APScheduler's `from_crontab` does NOT do this itself,
    so '1-5' would silently fire Tue-Sat instead of the expected Mon-Fri.
    Named tokens like 'mon-fri' pass through untouched."""

    def translate(tok: str) -> str:
        if not tok:
            return tok
        if "/" in tok:
            base, step = tok.split("/", 1)
            return f"{translate(base)}/{step}"
        if "-" in tok:
            a, b = tok.split("-", 1)
            return f"{translate(a)}-{translate(b)}"
        if tok.isdigit():
            return str((int(tok) - 1) % 7)
        return tok

    if field == "*":
        return field
    return ",".join(translate(p) for p in field.split(","))


def parse_cron(expr: str, tz: tzinfo = timezone.utc) -> CronTrigger:
    """Parse a 5-field crontab string with standard crontab day-of-week
    semantics, in the given timezone (default UTC). Always use this instead
    of `CronTrigger.from_crontab` directly so the DOW translation and the
    deployment's configured timezone both apply."""
    parts = expr.split()
    if len(parts) == 5:
        parts[4] = _translate_crontab_dow(parts[4])
        expr = " ".join(parts)
    return CronTrigger.from_crontab(expr, timezone=tz)

_INTERVAL_RE = re.compile(r"^\s*(\d+)\s*([smhdw])\s*$", re.IGNORECASE)
_INTERVAL_UNITS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
}


def parse_interval(value: object) -> timedelta | None:
    if value in (None, ""):
        return None
    match = _INTERVAL_RE.match(str(value))
    if not match:
        return None
    qty, unit = match.groups()
    return timedelta(seconds=int(qty) * _INTERVAL_UNITS[unit.lower()])


def _parse_iso(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class ScheduleEntry:
    name: str
    responsibility: str
    interval: str | None = None
    cron: str | None = None
    enabled: bool = True
    last_run: str | None = None
    guard: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "responsibility": self.responsibility,
        }
        if self.interval is not None:
            d["interval"] = self.interval
        if self.cron is not None:
            d["cron"] = self.cron
        d["enabled"] = self.enabled
        d["last_run"] = self.last_run
        if self.guard is not None:
            d["guard"] = self.guard
        return d


@dataclass
class Schedule:
    path: Path
    entries: list[ScheduleEntry] = field(default_factory=list)
    body: str = ""
    extra_metadata: dict[str, Any] = field(default_factory=dict)


def load_schedule(path: Path) -> Schedule:
    if not path.exists():
        return Schedule(path=path)
    post = frontmatter.load(path)
    fm = dict(post.metadata or {})
    raw_entries = fm.pop("entries", []) or []
    entries: list[ScheduleEntry] = []
    for raw in raw_entries:
        if not isinstance(raw, dict):
            log.warning("schedule entry not a mapping: %r", raw)
            continue
        try:
            entries.append(
                ScheduleEntry(
                    name=str(raw["name"]),
                    responsibility=str(raw["responsibility"]),
                    interval=str(raw["interval"])
                    if raw.get("interval") not in (None, "")
                    else None,
                    cron=str(raw["cron"])
                    if raw.get("cron") not in (None, "")
                    else None,
                    enabled=bool(raw.get("enabled", True)),
                    last_run=raw["last_run"].isoformat()
                    if isinstance(raw.get("last_run"), datetime)
                    else (
                        str(raw["last_run"])
                        if raw.get("last_run") not in (None, "")
                        else None
                    ),
                    guard=str(raw["guard"])
                    if raw.get("guard") not in (None, "")
                    else None,
                )
            )
        except KeyError as e:
            log.warning("schedule entry missing required field %s: %r", e, raw)
    return Schedule(path=path, entries=entries, body=post.content, extra_metadata=fm)


def save_schedule(schedule: Schedule) -> None:
    metadata = dict(schedule.extra_metadata)
    metadata["entries"] = [e.to_dict() for e in schedule.entries]
    post = frontmatter.Post(schedule.body, **metadata)
    schedule.path.parent.mkdir(parents=True, exist_ok=True)
    schedule.path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


def evaluate_schedule(
    schedule: Schedule, now: datetime, tz: tzinfo = timezone.utc
) -> tuple[list[ScheduleEntry], bool]:
    """Walk all entries and return (due_entries, mutated).

    Side effect: entries with a missing `last_run` get initialized to `now`
    (so a freshly-added entry waits for one full period before firing).
    The caller should `save_schedule` if `mutated` is True even when
    `due_entries` is empty.
    """
    due: list[ScheduleEntry] = []
    mutated = False
    for entry in schedule.entries:
        if not entry.enabled:
            continue
        if entry.interval and entry.cron:
            log.warning(
                "entry %s declares both interval and cron; using interval",
                entry.name,
            )
        last = _parse_iso(entry.last_run)
        if last is None:
            entry.last_run = now.isoformat()
            mutated = True
            continue
        if entry.interval:
            interval = parse_interval(entry.interval)
            if interval is None:
                log.warning(
                    "entry %s has unparseable interval %r; skipping",
                    entry.name, entry.interval,
                )
                continue
            if now - last >= interval:
                due.append(entry)
            continue
        if entry.cron:
            try:
                trigger = parse_cron(entry.cron, tz)
            except Exception as exc:
                log.warning(
                    "entry %s has invalid cron %r: %s; skipping",
                    entry.name, entry.cron, exc,
                )
                continue
            next_fire = trigger.get_next_fire_time(last, last)
            if next_fire is not None and next_fire <= now:
                due.append(entry)
            continue
        log.warning("entry %s has neither interval nor cron; skipping", entry.name)
    return due, mutated


def mark_fired(entry: ScheduleEntry, when: datetime) -> None:
    entry.last_run = when.isoformat()


def next_fire_time(
    entry: ScheduleEntry, now: datetime, tz: tzinfo = timezone.utc
) -> datetime | None:
    """Compute when this entry will next fire. Returns None if disabled or
    cadence is unparseable. If already overdue, returns the original
    next-fire time (which will be <= now)."""
    if not entry.enabled:
        return None
    last = _parse_iso(entry.last_run) or now
    if entry.interval:
        delta = parse_interval(entry.interval)
        if delta is None:
            return None
        return last + delta
    if entry.cron:
        try:
            trigger = parse_cron(entry.cron, tz)
        except Exception:
            return None
        return trigger.get_next_fire_time(last, last)
    return None


def render_task_for_entry(
    entry: ScheduleEntry, responsibility_path: Path
) -> tuple[str, str]:
    """Read the referenced responsibility and produce (title, body) for the
    concrete task to enqueue. The body wraps the responsibility's contract in
    a short framing header so the entity knows it's a scheduled execution
    (not a planning task) and ends with the `complete_task` reminder."""
    post = frontmatter.load(responsibility_path)
    fm = post.metadata or {}
    description = str(fm.get("description") or "").strip()
    resp_body = post.content.strip()
    title = entry.responsibility.replace("_", " ").strip().capitalize() or entry.responsibility

    lines: list[str] = [
        f"Scheduled execution of your standing responsibility "
        f"**{entry.responsibility}** (schedule entry `{entry.name}`).",
        "",
    ]
    if description:
        lines.append(description)
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(resp_body)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "When the work above is finished, call `complete_task` to mark this done."
    )
    return title, "\n".join(lines) + "\n"
