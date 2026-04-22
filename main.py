import logging
import threading

from harness.bootstrap import bootstrap_entity
from harness.config import load_settings
from harness.entity import Entity
from harness.runtime.status import WorkerStatus
from harness.runtime.worker import run_worker
from harness.ui.tui import run_tui


def main() -> None:
    settings = load_settings()
    bootstrap_entity(settings)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        filename=str(settings.worker_log_path),
    )

    settings.work_dir.mkdir(parents=True, exist_ok=True)

    chat_entity = Entity(settings)
    worker_entity = Entity(settings)

    status = WorkerStatus()
    stop_event = threading.Event()

    worker_thread = threading.Thread(
        target=run_worker,
        args=(
            worker_entity,
            status,
            stop_event,
            settings.tasks_dir,
            settings.schedules_dir,
            settings.worker_poll_interval,
        ),
        daemon=True,
        name="entity-worker",
    )
    worker_thread.start()

    try:
        run_tui(chat_entity, status, stop_event, settings.tasks_dir)
    finally:
        stop_event.set()
        worker_thread.join(timeout=5)


if __name__ == "__main__":
    main()
