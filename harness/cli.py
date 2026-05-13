import argparse
import logging
import os
import signal
import subprocess
import sys
import threading
import time

import uvicorn

from harness.bootstrap import bootstrap_entity
from harness.config import Settings, load_settings
from harness.entity import Entity
from harness.knowledge.ask import ask as knowledge_ask
from harness.runtime.lifecycle import (
    clear_pid_file,
    pid_alive,
    worker_already_running,
    write_pid_file,
)
from harness.runtime.status import FileBackedWorkerStatus, WorkerStatus
from harness.runtime.worker import run_worker


log = logging.getLogger(__name__)


def _setup(settings: Settings) -> None:
    bootstrap_entity(settings)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        filename=str(settings.worker_log_path),
    )
    settings.work_dir.mkdir(parents=True, exist_ok=True)


def run_headless(settings: Settings) -> None:
    existing = worker_already_running(settings.worker_pid_path)
    if existing is not None:
        msg = f"worker already running (pid {existing}); exiting"
        log.error(msg)
        print(msg, file=sys.stderr)
        sys.exit(1)

    write_pid_file(settings.worker_pid_path)
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    try:
        worker_entity = Entity(settings)
        status = WorkerStatus(status_file=settings.worker_status_path)
        run_worker(
            worker_entity,
            status,
            stop_event,
            settings.tasks_dir,
            settings.responsibilities_dir,
            settings.schedule_path,
            settings.scheduler_tz,
            settings.worker_poll_interval,
        )
    finally:
        clear_pid_file(settings.worker_pid_path)


def cmd_worker_start(settings: Settings) -> None:
    existing = worker_already_running(settings.worker_pid_path)
    if existing is not None:
        print(f"worker already running (pid {existing})", file=sys.stderr)
        sys.exit(1)

    proc = subprocess.Popen(
        [sys.executable, "-m", "harness.cli", "worker", "_run"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd=os.getcwd(),
    )

    deadline = time.time() + 5.0
    while time.time() < deadline:
        rc = proc.poll()
        if rc is not None:
            print(
                f"worker exited immediately (rc={rc}); see {settings.worker_log_path}",
                file=sys.stderr,
            )
            sys.exit(1)
        pid = worker_already_running(settings.worker_pid_path)
        if pid is not None:
            print(f"worker started (pid {pid})")
            return
        time.sleep(0.1)
    print("timed out waiting for worker to start; check logs", file=sys.stderr)
    sys.exit(1)


def cmd_worker_stop(settings: Settings) -> None:
    pid = worker_already_running(settings.worker_pid_path)
    if pid is None:
        print("no worker running")
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        print("no worker running")
        return

    deadline = time.time() + 10.0
    while time.time() < deadline:
        if not pid_alive(pid):
            print(f"worker stopped (pid {pid})")
            return
        time.sleep(0.1)
    print(
        f"worker (pid {pid}) did not exit after 10s; still running",
        file=sys.stderr,
    )
    sys.exit(1)


def cmd_worker_status(settings: Settings) -> None:
    pid = worker_already_running(settings.worker_pid_path)
    if pid is None:
        print("worker: not running")
        return
    print(f"worker: running (pid {pid})")
    snap = FileBackedWorkerStatus(settings.worker_status_path).snapshot()
    if snap.idle:
        print("state: idle")
        return
    title = snap.current_task or "<unknown>"
    filename = snap.current_filename or "?"
    print(f'state: working on "{title}" ({filename})')
    last_tool = snap.last_tool or "-"
    started = snap.started_at.isoformat() if snap.started_at else "-"
    print(f"step: {snap.step}  last tool: {last_tool}  started: {started}")


def cmd_ask(settings: Settings, question: str) -> None:
    answer = knowledge_ask(question, settings)
    print(answer)


def cmd_serve(settings: Settings, host: str, port: int) -> None:
    if not settings.web_password_hash:
        print(
            "WEB_PASSWORD_HASH is not set in .env.\n"
            "Generate one with: uv run python -m harness.web.auth hash <password>",
            file=sys.stderr,
        )
        sys.exit(1)
    from harness.web.app import create_app

    app = create_app(settings)
    uvicorn.run(app, host=host, port=port, log_level="info")


def main() -> None:
    parser = argparse.ArgumentParser(prog="ci")
    sub = parser.add_subparsers(dest="cmd", required=True)

    worker = sub.add_parser("worker", help="Manage the background worker.")
    worker_sub = worker.add_subparsers(dest="worker_cmd", required=True)
    worker_sub.add_parser("start", help="Start the worker as a detached background process.")
    worker_sub.add_parser("stop", help="Stop the running worker (SIGTERM).")
    worker_sub.add_parser("status", help="Print worker liveness and current activity.")
    worker_sub.add_parser("_run", help=argparse.SUPPRESS)

    serve = sub.add_parser(
        "serve",
        help="Run the web frontend (and an in-process worker if none is running).",
    )
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    ask = sub.add_parser(
        "ask",
        help="Ask a factual question against entity/knowledge/ via a single Haiku call.",
    )
    ask.add_argument("question", nargs="+", help="The question to ask.")

    args = parser.parse_args()

    settings = load_settings()
    _setup(settings)

    if args.cmd == "worker":
        if args.worker_cmd == "start":
            cmd_worker_start(settings)
        elif args.worker_cmd == "stop":
            cmd_worker_stop(settings)
        elif args.worker_cmd == "status":
            cmd_worker_status(settings)
        elif args.worker_cmd == "_run":
            run_headless(settings)
        else:
            parser.error(f"unknown worker subcommand: {args.worker_cmd}")
    elif args.cmd == "serve":
        host = args.host or settings.web_host
        port = args.port or settings.web_port
        cmd_serve(settings, host, port)
    elif args.cmd == "ask":
        cmd_ask(settings, " ".join(args.question))
    else:
        parser.error(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
