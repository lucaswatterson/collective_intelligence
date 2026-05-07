import logging
import os
from pathlib import Path


log = logging.getLogger(__name__)


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but is owned by a different user. Treat as alive.
        return True
    except OSError:
        return False
    return True


def worker_already_running(pid_path: Path) -> int | None:
    """Return the PID of a live worker recorded in `pid_path`, or None.

    A stale PID file (process gone) returns None; the caller is free to
    overwrite it.
    """
    try:
        text = pid_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except OSError as exc:
        log.warning("could not read pid file %s: %s", pid_path, exc)
        return None
    try:
        pid = int(text)
    except ValueError:
        log.warning("pid file %s is not an integer: %r", pid_path, text)
        return None
    if pid == os.getpid():
        # Our own pid was left in the file (shouldn't happen, but harmless).
        return None
    return pid if pid_alive(pid) else None


def write_pid_file(pid_path: Path) -> None:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")


def clear_pid_file(pid_path: Path) -> None:
    try:
        pid_path.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        log.warning("could not remove pid file %s: %s", pid_path, exc)
