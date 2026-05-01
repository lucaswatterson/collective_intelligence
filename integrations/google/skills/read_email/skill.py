import json
import shutil
import subprocess


GWS_MISSING = (
    "Error: `gws` CLI not installed. "
    "Install with: brew install googleworkspace-cli"
)

AUTH_HINT = (
    "Error: `gws` is not authenticated. Run: gws auth setup"
)

AUTH_KEYWORDS = ("auth", "credential", "token", "login", "consent", "unauthorized")


def run(**input) -> str:
    max_results = int(input.get("max_results") or 20)

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    try:
        result = subprocess.run(
            [gws, "gmail", "+triage", "--format", "json", "--max", str(max_results)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "Error: `gws gmail +triage` timed out after 30s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    messages = _parse_messages(result.stdout)
    if not messages:
        return "[0 unread]"

    return _format(messages[:max_results], total=len(messages))


def _parse_messages(stdout: str) -> list[dict]:
    """Tolerantly parse gws output: accept a JSON array, a single object,
    or NDJSON (one JSON value per line)."""
    text = stdout.strip()
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [m for m in parsed if isinstance(m, dict)]
        if isinstance(parsed, dict):
            for key in ("messages", "items", "results", "data"):
                inner = parsed.get(key)
                if isinstance(inner, list):
                    return [m for m in inner if isinstance(m, dict)]
            return [parsed]
    except json.JSONDecodeError:
        pass

    messages: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            messages.append(obj)
    return messages


def _format(messages: list[dict], total: int) -> str:
    shown = len(messages)
    header = f"[{total} unread]" if shown == total else f"[{total} unread, showing {shown}]"
    lines = [header]
    for m in messages:
        msg_id = _first(m, "id", "messageId", "message_id") or "?"
        date = _first(m, "date", "internalDate", "receivedAt", "timestamp") or "?"
        sender = _first(m, "from", "sender", "fromAddress") or "?"
        subject = _first(m, "subject", "title") or "(no subject)"
        snippet = _first(m, "snippet", "preview", "body") or ""
        snippet = " ".join(str(snippet).split())
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        line = f"{msg_id} | {date} | {sender} | {subject}"
        if snippet:
            line += f" — {snippet}"
        lines.append(line)
    return "\n".join(lines)


def _first(d: dict, *keys: str) -> str | None:
    for k in keys:
        v = d.get(k)
        if v:
            return str(v)
    return None
