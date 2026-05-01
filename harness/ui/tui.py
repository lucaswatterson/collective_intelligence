import threading
from datetime import datetime, timezone
from pathlib import Path

import frontmatter
from rich.console import Group
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Static, TextArea

from harness.entity import Entity
from harness.runtime.status import WorkerStatus
from harness.runtime.worker import active_responsibilities


BANNER_BIRTH = (
    "entity unborn · begin the birth conversation · "
    "tasks dormant until IDENTITY.md is committed"
)

_MAX_ENTRIES = 200

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_PRIORITY_LABEL: dict[str, tuple[str, str]] = {
    "high": ("[H]", "red"),
    "medium": ("[M]", "yellow"),
    "low": ("[L]", "dim"),
}


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
                    "created": str(fm.get("created", "")),
                })
        except Exception:
            continue
    tasks.sort(key=lambda t: (_PRIORITY_ORDER.get(t["priority"], 1), t["created"]))
    return tasks


def _format_relative(iso_string: str | None) -> str:
    if not iso_string:
        return "never"
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except ValueError:
        return iso_string
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    secs = int((datetime.now(timezone.utc) - dt).total_seconds())
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


def _render_responsibilities(resp_dir: Path) -> Group:
    items = active_responsibilities(resp_dir)
    if not items:
        return Group(Text("(no active responsibilities)", style="dim italic"))
    lines: list[Text] = []
    for r in items:
        rel = _format_relative(r.last_reviewed)
        rel_style = "yellow" if r.last_reviewed is None else "dim"
        lines.append(
            Text.assemble((r.name, "cyan"), ("  ·  ", "dim"), (rel, rel_style))
        )
    return Group(*lines)


def _render_tasks(status: WorkerStatus, tasks_dir: Path) -> Group:
    snap = status.snapshot()
    pending = _pending_tasks(tasks_dir)
    lines: list[Text] = []
    if snap.idle:
        lines.append(Text("💤 idle\nwatching for tasks", style="dim"))
    else:
        lines.append(Text.assemble(("⚙ ", "cyan"), (snap.current_task or "?", "bold cyan")))
        if snap.current_filename:
            lines.append(Text(snap.current_filename, style="dim"))
        lines.append(Text(""))
        lines.append(Text.assemble(("step  ", "dim"), (str(snap.step), "white")))
        if snap.last_tool:
            lines.append(Text.assemble(("tool  ", "dim"), (snap.last_tool, "magenta")))
        if snap.started_at is not None:
            secs = int((datetime.now() - snap.started_at).total_seconds())
            lines.append(Text.assemble(("time  ", "dim"), (f"{secs}s", "white")))

    if pending:
        lines.append(Text(""))
        lines.append(Text("── queued ──────────", style="dim"))
        for task in pending[:5]:
            pri = task["priority"]
            label, color = _PRIORITY_LABEL.get(pri, ("[M]", "yellow"))
            lines.append(Text.assemble((label + " ", color), (task["title"], "dim")))
        if len(pending) > 5:
            lines.append(Text(f"  … {len(pending) - 5} more", style="dim"))

    return Group(*lines)


class ChatInput(TextArea):
    """Multi-line input. Enter submits; Shift+Enter inserts a newline.

    Falls back gracefully on terminals that can't distinguish Shift+Enter
    from Enter — there, both will submit. Use Alt+Enter as an alternate
    newline binding for those terminals.

    Standard editing shortcuts inherited from TextArea: Ctrl+C copy,
    Ctrl+X cut, Ctrl+V paste, Ctrl+Z/Y undo/redo. Ctrl+A is rebound to
    select-all here (TextArea's default is emacs-style start-of-line).
    """

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False, priority=True),
        Binding("shift+enter", "newline", "Newline", show=False),
        Binding("alt+enter", "newline", "Newline", show=False),
        Binding("ctrl+a", "select_all", "Select all", show=False, priority=True),
    ]

    class Submitted(Message):
        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def action_submit(self) -> None:
        self.post_message(self.Submitted(self.text))

    def action_newline(self) -> None:
        self.insert("\n")


class EntityTUI(App):
    CSS = """
    #left {
        width: 2fr;
        height: 100%;
    }
    #right {
        width: 1fr;
        min-width: 32;
        max-width: 48;
        height: 100%;
    }
    #chat-scroll {
        height: 1fr;
        border: round green;
        padding: 0 1;
    }
    #chat { height: auto; }
    #input {
        height: auto;
        min-height: 6;
        max-height: 16;
        border: round green;
    }
    #resp {
        height: 1fr;
        border: round magenta;
        padding: 0 1;
    }
    #tasks {
        height: 1fr;
        border: round gray;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(
        self,
        entity: Entity,
        status: WorkerStatus,
        stop_event: threading.Event,
        tasks_dir: Path,
        responsibilities_dir: Path,
    ) -> None:
        super().__init__()
        self.entity = entity
        self.status = status
        self.stop_event = stop_event
        self.tasks_dir = tasks_dir
        self.responsibilities_dir = responsibilities_dir
        self._entries: list[Text] = []
        self._streaming: Text | None = None
        self._busy = False

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left"):
                with VerticalScroll(id="chat-scroll"):
                    yield Static("", id="chat")
                yield ChatInput(id="input", show_line_numbers=False)
            with Vertical(id="right"):
                yield Static("", id="resp")
                yield Static("", id="tasks")

    def on_mount(self) -> None:
        self.entity.begin_session()
        self.query_one("#chat-scroll", VerticalScroll).border_title = "entity"
        self.query_one("#resp", Static).border_title = "responsibilities"
        self.query_one("#tasks", Static).border_title = "tasks"
        self.query_one("#input", ChatInput).border_title = "you"
        if self.entity.in_birth:
            self._append_entry(Text(BANNER_BIRTH, style="dim italic"))
        self._refresh_panels()
        self.set_interval(1.0, self._refresh_panels)
        self.query_one("#input", ChatInput).focus()

    def on_unmount(self) -> None:
        self.stop_event.set()

    def _refresh_panels(self) -> None:
        self.query_one("#resp", Static).update(
            _render_responsibilities(self.responsibilities_dir)
        )
        self.query_one("#tasks", Static).update(
            _render_tasks(self.status, self.tasks_dir)
        )

    def _append_entry(self, text: Text) -> None:
        self._entries.append(text)
        if len(self._entries) > _MAX_ENTRIES:
            self._entries = self._entries[-_MAX_ENTRIES:]
        self._render_chat()

    def _render_chat(self) -> None:
        items: list[Text] = []
        for i, e in enumerate(self._entries):
            if i:
                items.append(Text(""))
            items.append(e)
        if self._streaming is not None:
            if items:
                items.append(Text(""))
            items.append(self._streaming)
        if not items:
            items.append(Text(""))
        self.query_one("#chat", Static).update(Group(*items))
        self.call_after_refresh(self._scroll_chat_end)

    def _scroll_chat_end(self) -> None:
        self.query_one("#chat-scroll", VerticalScroll).scroll_end(animate=False)

    def on_chat_input_submitted(self, event: "ChatInput.Submitted") -> None:
        text = event.value.strip()
        if not text:
            return
        if text.lower() in {"exit", "quit"}:
            self.exit()
            return
        if self._busy:
            return
        self.query_one("#input", ChatInput).text = ""
        self._append_entry(Text.assemble(("you › ", "bold cyan"), (text, "white")))
        self._begin_stream()
        self.run_turn(text)

    def _begin_stream(self) -> None:
        self._busy = True
        self._streaming = Text.assemble(("entity › ", "bold green"), ("", "white"))
        self._render_chat()
        self.query_one("#input", ChatInput).border_title = "thinking…"

    def _append_stream_chunk(self, chunk: str) -> None:
        if self._streaming is None:
            return
        self._streaming.append(chunk, "white")
        self._render_chat()

    def _set_tool(self, name: str) -> None:
        self.query_one("#input", ChatInput).border_title = f"calling {name}…"

    def _finish_stream(self, error: str | None = None) -> None:
        if self._streaming is not None:
            self._entries.append(self._streaming)
            self._streaming = None
            if len(self._entries) > _MAX_ENTRIES:
                self._entries = self._entries[-_MAX_ENTRIES:]
        if error:
            self._entries.append(Text(f"[chat error: {error}]", style="red"))
        self._render_chat()
        self.query_one("#input", ChatInput).border_title = "you"
        self._busy = False

    @work(thread=True, exclusive=True)
    def run_turn(self, text: str) -> None:
        def on_text(chunk: str) -> None:
            self.call_from_thread(self._append_stream_chunk, chunk)

        def on_tool_use(name: str) -> None:
            self.call_from_thread(self._set_tool, name)

        try:
            self.entity.turn(text, on_text=on_text, on_tool_use=on_tool_use)
            self.call_from_thread(self._finish_stream)
        except Exception as exc:
            err = str(exc)
            self.call_from_thread(self._finish_stream, err)


def run_tui(
    entity: Entity,
    status: WorkerStatus,
    stop_event: threading.Event,
    tasks_dir: Path,
    responsibilities_dir: Path,
) -> None:
    app = EntityTUI(entity, status, stop_event, tasks_dir, responsibilities_dir)
    app.run()
