import io
import select
import sys
import termios
import threading
import time
import tty
from datetime import datetime
from pathlib import Path

import frontmatter
from rich.console import Console, ConsoleOptions, Group, RenderResult
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.segment import Segment
from rich.text import Text

from harness.entity import Entity
from harness.runtime.status import WorkerStatus


BANNER_BORN = "entity online · type and press enter · Ctrl-C to quit · tasks running"
BANNER_BIRTH = (
    "entity unborn · begin the birth conversation\n"
    "tasks dormant until IDENTITY.md is committed"
)


class ChatBuffer:
    """Thread-safe rolling buffer of rendered chat entries."""

    def __init__(self, max_entries: int = 200) -> None:
        self._lock = threading.Lock()
        self._entries: list[Text] = []
        self._streaming: Text | None = None
        self._max = max_entries
        self._scroll_offset = 0  # lines hidden from the bottom of the view

    def append(self, text: Text) -> None:
        with self._lock:
            self._entries.append(text)
            if len(self._entries) > self._max:
                self._entries = self._entries[-self._max :]

    def set_streaming(self, text: Text) -> None:
        with self._lock:
            self._streaming = text

    def commit_streaming(self) -> None:
        with self._lock:
            if self._streaming is not None:
                self._entries.append(self._streaming)
                self._streaming = None
                if len(self._entries) > self._max:
                    self._entries = self._entries[-self._max :]

    def render(self) -> Group:
        with self._lock:
            entries = list(self._entries)
            streaming = self._streaming
        items: list[Text] = []
        for i, e in enumerate(entries):
            if i:
                items.append(Text(""))
            items.append(e)
        if streaming is not None:
            if items:
                items.append(Text(""))
            items.append(streaming)
        if not items:
            items.append(Text(""))
        return Group(*items)

    def scroll_up(self, n: int) -> None:
        with self._lock:
            self._scroll_offset += n

    def scroll_down(self, n: int) -> None:
        with self._lock:
            self._scroll_offset = max(0, self._scroll_offset - n)

    def scroll_to_top(self) -> None:
        with self._lock:
            self._scroll_offset = 10**9  # clamped at render time

    def reset_scroll(self) -> None:
        with self._lock:
            self._scroll_offset = 0

    def scroll_offset(self) -> int:
        with self._lock:
            return self._scroll_offset


class InputState:
    """Keystroke-driven single-line input buffer with submission handoff."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buffer = ""
        self._submitted: str | None = None
        self._busy = False

    def key(self, ch: str) -> None:
        with self._lock:
            if self._busy:
                return
            if ch in ("\r", "\n"):
                if self._buffer.strip():
                    self._submitted = self._buffer
                    self._buffer = ""
            elif ch in ("\x7f", "\x08"):  # backspace / ctrl-h
                self._buffer = self._buffer[:-1]
            elif ch == "\x15":  # ctrl-u — clear line
                self._buffer = ""
            elif ch < " ":  # ignore other control chars
                return
            else:
                self._buffer += ch

    def take_submission(self) -> str | None:
        with self._lock:
            s = self._submitted
            self._submitted = None
            return s

    def set_busy(self, busy: bool) -> None:
        with self._lock:
            self._busy = busy

    def snapshot(self) -> tuple[str, bool]:
        with self._lock:
            return self._buffer, self._busy


class _TailCropped:
    """Renderable that crops its content from the TOP so the newest lines
    stay visible, with optional scrollback offset for reading older content."""

    def __init__(self, renderable: Group, scroll_offset: int = 0) -> None:
        self._renderable = renderable
        self._scroll_offset = scroll_offset

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        height = options.height if options.height is not None else options.max_height
        # Render against an uncapped height so long content isn't bottom-cropped
        # before we get a chance to slice it ourselves.
        render_options = options.update(height=None)
        lines = console.render_lines(self._renderable, render_options, pad=False)
        if height is not None and len(lines) > height:
            max_offset = len(lines) - height
            offset = min(self._scroll_offset, max_offset)
            end = len(lines) - offset
            start = end - height
            lines = lines[start:end]
        for line in lines:
            yield from line
            yield Segment.line()


def _chat_body_panel(buffer: ChatBuffer) -> Panel:
    offset = buffer.scroll_offset()
    title = "chat" if offset == 0 else f"chat · scrolled (End to catch up)"
    return Panel(
        _TailCropped(buffer.render(), scroll_offset=offset),
        title=title,
        border_style="green" if offset == 0 else "yellow",
        padding=(0, 1),
    )


def _input_prompt(input_state: InputState) -> Text:
    text_buffer, busy = input_state.snapshot()
    if busy:
        return Text.assemble(
            ("entity › ", "bold green"),
            ("thinking…", "dim italic"),
        )
    return Text.assemble(
        ("you › ", "bold cyan"),
        (text_buffer, "white"),
        ("▎", "bold white"),
    )


def _input_panel_height(prompt: Text, chat_width: int, max_height: int) -> int:
    """Total panel height (incl. borders) needed to render prompt without crop."""
    inner = max(1, chat_width - 4)  # 2 border cols + 2 padding cols
    measure = Console(width=inner, file=io.StringIO(), force_terminal=False)
    lines = measure.render_lines(prompt, pad=False)
    return max(3, min(max_height, max(1, len(lines)) + 2))


def _chat_panel_width(console: Console) -> int:
    """Mirror Layout's split_row math for the chat column.

    Root: chat ratio=2, right ratio=1 with minimum_size=28.
    Rich satisfies minimums first, then distributes remaining width by ratio.
    """
    total = console.size.width
    chat_min, right_min = 1, 28
    remaining = max(0, total - chat_min - right_min)
    return chat_min + (remaining * 2) // 3


def _self_image_panel(entity: Entity) -> Panel:
    path = entity.settings.self_image_path
    if path.exists() and path.read_text(encoding="utf-8").strip():
        body: Text = Text(path.read_text(encoding="utf-8").rstrip("\n"), style="cyan")
    else:
        body = Text(
            "(no self-image yet)\n\n"
            "write ASCII art to\nentity/self_image.txt\nand it appears here",
            style="dim italic",
        )
    return Panel(body, border_style="magenta", padding=(0, 1))


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_PRIORITY_LABEL: dict[str, tuple[str, str]] = {
    "high": ("[H]", "red"),
    "medium": ("[M]", "yellow"),
    "low": ("[L]", "dim"),
}


def _pending_tasks(tasks_dir: Path) -> list[dict]:
    tasks = []
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


def _tasks_panel(status: WorkerStatus, tasks_dir: Path) -> Panel:
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

    border = "grey50" if snap.idle else "cyan"
    return Panel(Group(*lines), title="tasks", border_style=border, padding=(1, 1))


def _read_escape() -> str | None:
    """Read the rest of an ANSI escape sequence after ESC has been consumed.

    Returns a symbolic key name ("up", "down", "page_up", "page_down",
    "home", "end") for recognized sequences, or None for anything else
    (which is swallowed so it doesn't leak into the input buffer).
    """
    try:
        nxt = sys.stdin.read(1)
    except Exception:
        return None
    if nxt != "[":
        return None
    params = ""
    while True:
        c = sys.stdin.read(1)
        if not c:
            return None
        if "\x40" <= c <= "\x7e":
            seq = params + c
            return {
                "A": "up",
                "B": "down",
                "5~": "page_up",
                "6~": "page_down",
                "H": "home",
                "F": "end",
            }.get(seq)
        params += c


def run_tui(
    entity: Entity,
    status: WorkerStatus,
    stop_event: threading.Event,
    tasks_dir: Path,
) -> None:
    console = Console()
    entity.begin_session()

    buffer = ChatBuffer()
    input_state = InputState()
    banner = BANNER_BIRTH if entity.in_birth else BANNER_BORN
    buffer.append(Text(banner, style="dim italic"))

    layout = Layout()
    layout.split_row(
        Layout(name="chat", ratio=2),
        Layout(name="right", ratio=1, minimum_size=28),
    )
    layout["chat"].split_column(
        Layout(name="chat_body", ratio=1),
        Layout(name="chat_input", size=3),
    )
    layout["right"].split_column(
        Layout(name="self_image", ratio=1),
        Layout(name="tasks", ratio=1),
    )

    def refresh() -> None:
        prompt = _input_prompt(input_state)
        chat_width = _chat_panel_width(console)
        max_input = max(3, console.size.height // 2)
        new_size = _input_panel_height(prompt, chat_width, max_input)
        if layout["chat_input"].size != new_size:
            layout["chat_input"].size = new_size
        layout["chat_body"].update(_chat_body_panel(buffer))
        layout["chat_input"].update(
            Panel(prompt, border_style="green", padding=(0, 1))
        )
        layout["self_image"].update(_self_image_panel(entity))
        layout["tasks"].update(_tasks_panel(status, tasks_dir))

    refresh()

    live_stop = threading.Event()

    def run_turn(text: str) -> None:
        buffer.reset_scroll()
        buffer.append(Text.assemble(("you › ", "bold cyan"), (text, "white")))
        streaming = Text.assemble(("entity › ", "bold green"), ("", "white"))
        buffer.set_streaming(streaming)
        input_state.set_busy(True)

        def on_text(chunk: str) -> None:
            streaming.append(chunk)

        try:
            entity.turn(text, on_text=on_text)
            buffer.commit_streaming()
        except Exception as exc:
            buffer.commit_streaming()
            buffer.append(Text(f"[chat error: {exc}]", style="red"))
        finally:
            input_state.set_busy(False)

    fd = sys.stdin.fileno()
    old_term = termios.tcgetattr(fd)

    with Live(
        layout,
        console=console,
        refresh_per_second=10,
        screen=True,
    ):
        def ticker() -> None:
            while not live_stop.wait(0.1):
                refresh()

        threading.Thread(target=ticker, daemon=True).start()

        turn_thread: threading.Thread | None = None
        try:
            tty.setcbreak(fd)
            while True:
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    ch = sys.stdin.read(1)
                    if ch == "\x03":  # Ctrl-C
                        break
                    if ch == "\x04" and not input_state.snapshot()[0]:
                        break  # Ctrl-D on empty line
                    if ch == "\x1b":  # ESC — parse CSI sequence
                        key = _read_escape()
                        if key == "page_up":
                            buffer.scroll_up(10)
                        elif key == "page_down":
                            buffer.scroll_down(10)
                        elif key == "up":
                            buffer.scroll_up(1)
                        elif key == "down":
                            buffer.scroll_down(1)
                        elif key == "home":
                            buffer.scroll_to_top()
                        elif key == "end":
                            buffer.reset_scroll()
                        continue
                    input_state.key(ch)

                submission = input_state.take_submission()
                if submission is not None:
                    lowered = submission.strip().lower()
                    if lowered in {"exit", "quit"}:
                        break
                    # Block further submissions until this turn finishes;
                    # run_turn handles the busy flag. Use a thread so the
                    # ticker can keep refreshing and Ctrl-C stays responsive.
                    if turn_thread is not None and turn_thread.is_alive():
                        turn_thread.join()
                    turn_thread = threading.Thread(
                        target=run_turn, args=(submission,), daemon=True
                    )
                    turn_thread.start()

                if stop_event.is_set():
                    break
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_term)
            if turn_thread is not None and turn_thread.is_alive():
                turn_thread.join(timeout=5)
            live_stop.set()
            stop_event.set()
