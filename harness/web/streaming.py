import asyncio
import html
import logging
import secrets
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from harness.entity import Entity


log = logging.getLogger(__name__)

_SENTINEL = object()


def sse_event(event: str, data: str) -> bytes:
    """Encode an SSE frame. `data` may be multi-line; each line is its own `data:`."""
    lines = data.splitlines() or [""]
    payload = "".join(f"data: {line}\n" for line in lines)
    return f"event: {event}\n{payload}\n".encode("utf-8")


@dataclass
class TurnHandle:
    token: str
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    task: asyncio.Task | None = None


class TurnBroker:
    """In-memory registry of in-flight turns keyed by an opaque token.

    Single-user app: typically only one turn live at a time, but tokens keep
    stale connections from crossing wires.
    """

    def __init__(self) -> None:
        self._turns: dict[str, TurnHandle] = {}

    def start(self, entity: Entity, user_input: str) -> TurnHandle:
        token = secrets.token_urlsafe(12)
        handle = TurnHandle(token=token)
        loop = asyncio.get_running_loop()

        def on_text(chunk: str) -> None:
            loop.call_soon_threadsafe(handle.queue.put_nowait, ("chunk", chunk))

        def on_tool_use(name: str) -> None:
            loop.call_soon_threadsafe(handle.queue.put_nowait, ("tool", name))

        async def runner() -> None:
            try:
                await asyncio.to_thread(
                    entity.turn,
                    user_input,
                    on_text=on_text,
                    on_tool_use=on_tool_use,
                )
                await handle.queue.put(("done", ""))
            except Exception as exc:
                log.exception("turn failed")
                await handle.queue.put(("error", str(exc)))
            finally:
                await handle.queue.put(_SENTINEL)

        handle.task = asyncio.create_task(runner())
        self._turns[token] = handle
        return handle

    async def consume(self, token: str) -> AsyncIterator[bytes]:
        handle = self._turns.get(token)
        if handle is None:
            yield sse_event("error", "<span class='err'>unknown turn token</span>")
            return
        try:
            while True:
                item = await handle.queue.get()
                if item is _SENTINEL:
                    break
                event, payload = item  # type: ignore[misc]
                if event == "chunk":
                    yield sse_event("chunk", html.escape(payload))
                elif event == "tool":
                    yield sse_event(
                        "tool",
                        f"<span class='tool'>· {html.escape(payload)}</span>",
                    )
                elif event == "done":
                    yield sse_event("done", "")
                elif event == "error":
                    yield sse_event(
                        "error",
                        f"<span class='err'>error: {html.escape(payload)}</span>",
                    )
        finally:
            self._turns.pop(token, None)
            if handle.task and not handle.task.done():
                handle.task.cancel()
