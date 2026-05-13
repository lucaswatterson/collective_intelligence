from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from harness.config import Settings
from harness.entity import Entity
from harness.web.streaming import TurnBroker


def _entity_name(identity_path: Path) -> str:
    if not identity_path.exists():
        return "entity"
    try:
        for raw in identity_path.read_text().splitlines():
            line = raw.strip()
            if line.startswith("# "):
                return line[2:].strip() or "entity"
    except OSError:
        pass
    return "entity"


def build_chat_router(
    templates: Jinja2Templates,
    get_entity,
    broker: TurnBroker,
    settings: Settings,
) -> APIRouter:
    router = APIRouter()

    @router.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        entity: Entity = get_entity()
        return templates.TemplateResponse(
            request,
            "chat.html",
            {
                "in_birth": entity.in_birth,
                "entity_name": _entity_name(settings.identity_path),
            },
        )

    @router.post("/turn", response_class=HTMLResponse)
    async def turn(request: Request, message: str = Form(...)) -> HTMLResponse:
        text = message.strip()
        if not text:
            return HTMLResponse("", status_code=204)
        entity: Entity = get_entity()
        handle = broker.start(entity, text)
        return templates.TemplateResponse(
            request,
            "_turn.html",
            {"user_message": text, "token": handle.token},
        )

    @router.get("/turn/stream/{token}")
    async def turn_stream(token: str) -> StreamingResponse:
        return StreamingResponse(
            broker.consume(token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    return router
