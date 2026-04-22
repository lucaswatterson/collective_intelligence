import threading
from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True)
class WorkerSnapshot:
    idle: bool
    current_task: str | None
    current_filename: str | None
    step: int
    last_tool: str | None
    started_at: datetime | None


class WorkerStatus:
    """Thread-safe status surface for the worker, read by the UI."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snap = WorkerSnapshot(
            idle=True,
            current_task=None,
            current_filename=None,
            step=0,
            last_tool=None,
            started_at=None,
        )

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

    def record_tool(self, tool_name: str) -> None:
        with self._lock:
            self._snap = replace(
                self._snap,
                step=self._snap.step + 1,
                last_tool=tool_name,
            )

    def finish(self) -> None:
        with self._lock:
            self._snap = WorkerSnapshot(
                idle=True,
                current_task=None,
                current_filename=None,
                step=0,
                last_tool=None,
                started_at=None,
            )
