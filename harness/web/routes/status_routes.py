import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import frontmatter
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from harness.config import Settings
from harness.runtime.schedule import load_schedule, next_fire_time
from harness.web.markdown_render import render_markdown
from harness.web.streaming import sse_event


log = logging.getLogger(__name__)

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _pending_tasks(tasks_dir: Path) -> list[dict]:
    tasks: list[dict] = []
    if not tasks_dir.exists():
        return tasks
    for path in sorted(tasks_dir.glob("*.md")):
        if path.name.startswith("."):
            continue
        try:
            post = frontmatter.load(path)
            fm = post.metadata or {}
            if fm.get("status") == "todo":
                tasks.append({
                    "title": fm.get("title", path.stem),
                    "priority": str(fm.get("priority", "medium")),
                    "filename": path.name,
                    "created": str(fm.get("created", "")),
                })
        except Exception:
            continue
    tasks.sort(key=lambda t: (_PRIORITY_ORDER.get(t["priority"], 1), t["created"]))
    return tasks


def _format_past(iso_string: str | None, now: datetime) -> str:
    if not iso_string:
        return "never"
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except ValueError:
        return iso_string
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    secs = int((now - dt).total_seconds())
    if secs < 60:
        return f"{max(secs, 0)}s ago"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m ago"
    hrs = mins // 60
    if hrs < 24:
        return f"{hrs}h ago"
    days = hrs // 24
    if days < 7:
        return f"{days}d ago"
    return f"{days // 7}w ago"


def _format_future(target: datetime | None, now: datetime, tz: ZoneInfo) -> str:
    if target is None:
        return "—"
    secs = int((target - now).total_seconds())
    if secs <= 0:
        return "due"
    if secs < 60:
        return f"in {secs}s"
    mins = secs // 60
    if mins < 60:
        return f"in {mins}m"
    local = target.astimezone(tz)
    today = now.astimezone(tz).date()
    days = (local.date() - today).days
    clock = local.strftime("%-I:%M%p").lower()
    if days == 0:
        return clock
    if days == 1:
        return f"tom {clock}"
    if days < 7:
        return f"{local.strftime('%a').lower()} {clock}"
    return local.strftime("%Y-%m-%d")


def _schedule_view(settings: Settings) -> list[dict]:
    schedule = load_schedule(settings.schedule_path)
    now = datetime.now(timezone.utc)
    entries = []
    for entry in schedule.entries:
        nxt = next_fire_time(entry, now, settings.scheduler_tz) if entry.enabled else None
        entries.append({
            "name": entry.name,
            "responsibility": entry.responsibility,
            "enabled": entry.enabled,
            "next_str": _format_future(nxt, now, settings.scheduler_tz),
            "last_str": _format_past(entry.last_run, now),
            "overdue": nxt is not None and nxt <= now,
        })
    return entries


def _render_status_fragment(templates: Jinja2Templates, get_status, settings: Settings) -> str:
    snap = get_status().snapshot()
    template = templates.get_template("_status.html")
    return template.render(
        worker=snap,
        tasks=_pending_tasks(settings.tasks_dir),
        schedule=_schedule_view(settings),
        now=datetime.now(timezone.utc),
    )


def _recent_invocations(completed_dir: Path, schedule_name: str, now: datetime, limit: int = 5) -> list[dict]:
    if not completed_dir.exists():
        return []
    matches: list[dict] = []
    for path in completed_dir.glob("*.md"):
        if path.name.startswith("."):
            continue
        try:
            post = frontmatter.load(path)
            fm = post.metadata or {}
        except Exception:
            continue
        if fm.get("schedule_entry") != schedule_name:
            continue
        completed = fm.get("completed")
        matches.append({
            "title": fm.get("title", path.stem),
            "filename": path.name,
            "completed": str(completed) if completed else "",
            "ago": _format_past(str(completed) if completed else None, now),
        })
    matches.sort(key=lambda m: m["completed"], reverse=True)
    return matches[:limit]


def _format_iso_local(iso_string: str | None, tz: ZoneInfo) -> str:
    if not iso_string:
        return "never"
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except ValueError:
        return iso_string
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def _schedule_detail(settings: Settings, name: str) -> dict | None:
    schedule = load_schedule(settings.schedule_path)
    entry = next((e for e in schedule.entries if e.name == name), None)
    if entry is None:
        return None
    now = datetime.now(timezone.utc)
    nxt = next_fire_time(entry, now, settings.scheduler_tz) if entry.enabled else None
    responsibility_path = settings.responsibilities_dir / f"{entry.responsibility}.md"
    responsibility_html: str | None = None
    if responsibility_path.exists():
        try:
            post = frontmatter.load(responsibility_path)
            body = (post.content or "").strip()
        except Exception:
            body = responsibility_path.read_text(errors="replace")
        if body:
            responsibility_html = render_markdown(body)
    return {
        "name": entry.name,
        "responsibility": entry.responsibility,
        "responsibility_exists": responsibility_path.exists(),
        "responsibility_html": responsibility_html,
        "interval": entry.interval,
        "cron": entry.cron,
        "enabled": entry.enabled,
        "guard": entry.guard,
        "last_run_iso": entry.last_run or "",
        "last_run_local": _format_iso_local(entry.last_run, settings.scheduler_tz),
        "last_run_ago": _format_past(entry.last_run, now),
        "next_local": _format_iso_local(nxt.isoformat(), settings.scheduler_tz) if nxt else "—",
        "next_rel": _format_future(nxt, now, settings.scheduler_tz),
        "overdue": nxt is not None and nxt <= now,
        "recent": _recent_invocations(settings.tasks_dir / ".completed", entry.name, now),
    }


def build_status_router(
    templates: Jinja2Templates,
    get_status,
    settings: Settings,
) -> APIRouter:
    router = APIRouter()

    @router.get("/status", response_class=HTMLResponse)
    def status_panel() -> HTMLResponse:
        return HTMLResponse(_render_status_fragment(templates, get_status, settings))

    @router.get("/schedule/{name}/details", response_class=HTMLResponse)
    def schedule_details(name: str) -> HTMLResponse:
        detail = _schedule_detail(settings, name)
        if detail is None:
            raise HTTPException(status_code=404, detail="schedule entry not found")
        html = templates.get_template("_schedule_modal.html").render(entry=detail)
        return HTMLResponse(html)

    @router.get("/status/stream")
    async def status_stream(request: Request) -> StreamingResponse:
        async def gen():
            status_path = settings.worker_status_path
            last_mtime = -1.0
            last_tasks_mtime = -1.0
            last_schedule_mtime = -1.0
            yield sse_event(
                "message",
                _render_status_fragment(templates, get_status, settings),
            )
            while True:
                if await request.is_disconnected():
                    return
                changed = False
                for path, last in (
                    (status_path, last_mtime),
                    (settings.tasks_dir, last_tasks_mtime),
                    (settings.schedule_path, last_schedule_mtime),
                ):
                    try:
                        m = path.stat().st_mtime
                    except FileNotFoundError:
                        continue
                    if m != last:
                        changed = True
                        if path is status_path:
                            last_mtime = m
                        elif path is settings.tasks_dir:
                            last_tasks_mtime = m
                        else:
                            last_schedule_mtime = m
                if changed:
                    yield sse_event(
                        "message",
                        _render_status_fragment(templates, get_status, settings),
                    )
                await asyncio.sleep(0.5)

        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    return router
