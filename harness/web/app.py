import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from harness.config import Settings
from harness.entity import Entity
from harness.runtime.lifecycle import (
    clear_pid_file,
    worker_already_running,
    write_pid_file,
)
from harness.runtime.status import FileBackedWorkerStatus, WorkerStatus
from harness.runtime.worker import run_worker
from harness.web.auth import is_logged_in, resolve_session_secret
from harness.web.routes.auth_routes import attach_login_routes
from harness.web.routes.chat import build_chat_router
from harness.web.routes.status_routes import build_status_router
from harness.web.streaming import TurnBroker


log = logging.getLogger(__name__)


WEB_ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = WEB_ROOT / "templates"
STATIC_DIR = WEB_ROOT / "static"


def create_app(settings: Settings) -> FastAPI:
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
    broker = TurnBroker()

    chat_entity = Entity(settings)
    chat_entity.begin_session()

    state: dict = {"status": None, "stop_event": None, "owns_worker": False, "thread": None}

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        existing_pid = worker_already_running(settings.worker_pid_path)
        if existing_pid is None:
            log.info("no external worker detected; starting in-process worker thread")
            stop_event = threading.Event()
            status = WorkerStatus(status_file=settings.worker_status_path)
            worker_entity = Entity(settings)
            write_pid_file(settings.worker_pid_path)
            thread = threading.Thread(
                target=run_worker,
                args=(
                    worker_entity,
                    status,
                    stop_event,
                    settings.tasks_dir,
                    settings.responsibilities_dir,
                    settings.schedule_path,
                    settings.scheduler_tz,
                    settings.worker_poll_interval,
                ),
                daemon=True,
                name="entity-worker",
            )
            thread.start()
            state.update(status=status, stop_event=stop_event, owns_worker=True, thread=thread)
        else:
            log.info("attaching to existing worker (pid %s)", existing_pid)
            state["status"] = FileBackedWorkerStatus(settings.worker_status_path)
            state["owns_worker"] = False

        try:
            yield
        finally:
            if state.get("owns_worker"):
                state["stop_event"].set()
                thread = state.get("thread")
                if thread is not None:
                    thread.join(timeout=5)
                clear_pid_file(settings.worker_pid_path)

    app = FastAPI(lifespan=lifespan)

    # Middleware order: Starlette runs the LAST-added middleware first (outermost).
    # We want SessionMiddleware to run before the auth-gate, so add it last.
    @app.middleware("http")
    async def redirect_unauthed(request: Request, call_next):
        path = request.url.path
        public = (
            path == "/login"
            or path.startswith("/static/")
            or path == "/favicon.ico"
        )
        if not public and not is_logged_in(request):
            return RedirectResponse(url="/login", status_code=303)
        return await call_next(request)

    app.add_middleware(
        SessionMiddleware,
        secret_key=resolve_session_secret(settings),
        same_site="lax",
        https_only=False,
    )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(
        attach_login_routes(templates, lambda: settings.web_password_hash)
    )
    app.include_router(
        build_chat_router(templates, lambda: chat_entity, broker, settings)
    )
    app.include_router(
        build_status_router(templates, lambda: state["status"], settings)
    )

    return app
