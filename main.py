import logging
import threading

from collective.config import load_settings
from collective.entity import Entity
from collective.runtime.status import WorkerStatus
from collective.runtime.worker import run_worker
from collective.ui.tui import run_tui


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        filename="entity/worker.log",
    )

    settings = load_settings()
    settings.work_dir.mkdir(parents=True, exist_ok=True)

    chat_entity = Entity(settings)
    worker_entity = Entity(settings)

    status = WorkerStatus()
    stop_event = threading.Event()

    # Only run the worker once the entity has been born; if IDENTITY.md is
    # missing the birth flow happens in chat and the worker would error out.
    worker_thread: threading.Thread | None = None
    if not worker_entity.needs_birth():
        worker_thread = threading.Thread(
            target=run_worker,
            args=(
                worker_entity,
                status,
                stop_event,
                settings.tasks_dir,
                settings.worker_poll_interval,
            ),
            daemon=True,
            name="entity-worker",
        )
        worker_thread.start()

    try:
        run_tui(chat_entity, status, stop_event)
    finally:
        stop_event.set()
        if worker_thread is not None:
            worker_thread.join(timeout=5)


if __name__ == "__main__":
    main()
