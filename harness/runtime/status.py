import json
import logging
import os
import threading
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerSnapshot:
    idle: bool
    current_task: str | None
    current_filename: str | None
    step: int
    last_tool: str | None
    started_at: datetime | None


_IDLE = WorkerSnapshot(
    idle=True,
    current_task=None,
    current_filename=None,
    step=0,
    last_tool=None,
    started_at=None,
)


def _snap_to_dict(snap: WorkerSnapshot) -> dict:
    return {
        "idle": snap.idle,
        "current_task": snap.current_task,
        "current_filename": snap.current_filename,
        "step": snap.step,
        "last_tool": snap.last_tool,
        "started_at": snap.started_at.isoformat() if snap.started_at else None,
    }


def _snap_from_dict(d: dict) -> WorkerSnapshot:
    started = d.get("started_at")
    return WorkerSnapshot(
        idle=bool(d.get("idle", True)),
        current_task=d.get("current_task"),
        current_filename=d.get("current_filename"),
        step=int(d.get("step", 0)),
        last_tool=d.get("last_tool"),
        started_at=datetime.fromisoformat(started) if started else None,
    )


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)


class WorkerStatus:
    """Thread-safe status surface for the worker, read by the UI.

    If `status_file` is set, every state change is also written atomically to
    that path as JSON so a TUI in another process can read it.
    """

    def __init__(self, status_file: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._snap = _IDLE
        self._status_file = status_file
        if self._status_file is not None:
            self._persist(self._snap)

    def snapshot(self) -> WorkerSnapshot:
        with self._lock:
            return self._snap

    def start_task(self, title: str, filename: str) -> None:
        with self._lock:
            self._snap = WorkerSnapshot(
                idle=False,
                current_task=title,
                current_filename=filename,
                step=0,
                last_tool=None,
                started_at=datetime.now(),
            )
            snap = self._snap
        self._persist(snap)

    def record_tool(self, tool_name: str) -> None:
        with self._lock:
            self._snap = replace(
                self._snap,
                step=self._snap.step + 1,
                last_tool=tool_name,
            )
            snap = self._snap
        self._persist(snap)

    def finish(self) -> None:
        with self._lock:
            self._snap = _IDLE
            snap = self._snap
        self._persist(snap)

    def _persist(self, snap: WorkerSnapshot) -> None:
        if self._status_file is None:
            return
        try:
            _atomic_write_json(self._status_file, _snap_to_dict(snap))
        except Exception as exc:
            log.warning("failed to write status file %s: %s", self._status_file, exc)


class FileBackedWorkerStatus:
    """Read-only `.snapshot()` adapter that reads from a status file written
    by a `WorkerStatus` running in another process. Returns idle if the file
    is missing or unreadable."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def snapshot(self) -> WorkerSnapshot:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return _IDLE
        except Exception as exc:
            log.debug("status file unreadable (%s): %s", self._path, exc)
            return _IDLE
        try:
            return _snap_from_dict(data)
        except Exception as exc:
            log.debug("status file malformed (%s): %s", self._path, exc)
            return _IDLE
