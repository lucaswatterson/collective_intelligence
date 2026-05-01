import json
import shutil
import subprocess


GWS_MISSING = (
    "Error: `gws` CLI not installed. "
    "Install with: brew install googleworkspace-cli"
)

AUTH_HINT = "Error: `gws` is not authenticated. Run: gws auth setup"

AUTH_KEYWORDS = ("auth", "credential", "token", "login", "consent", "unauthorized")

SNIPPET_LIMIT = 200


def run(**input) -> str:
    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    max_spaces = int(input.get("max_spaces") or 50)
    max_per_space = int(input.get("max_messages_per_space") or 20)

    target_space = input.get("space")
    if target_space:
        spaces = [{"name": str(target_space)}]
    else:
        spaces_result = _list_spaces(gws, max_spaces)
        if isinstance(spaces_result, str):
            return spaces_result
        spaces = spaces_result

    sections: list[str] = []
    errors: list[str] = []
    total_unread = 0

    for space in spaces:
        name = space.get("name")
        if not name:
            continue

        last_read = _get_last_read(gws, name)
        if isinstance(last_read, _Err):
            errors.append(f"{name}: read-state lookup failed — {last_read.msg}")
            continue

        messages = _list_unread(gws, name, last_read, max_per_space)
        if isinstance(messages, _Err):
            errors.append(f"{name}: message list failed — {messages.msg}")
            continue

        if not messages:
            continue

        space_type = space.get("spaceType") or space.get("type") or ""
        header = f"=== {name}"
        if space_type:
            header += f" ({space_type})"
        header += f" — {len(messages)} unread"
        if last_read:
            header += f" since {last_read}"
        header += " ==="
        section_lines = [header]
        for m in messages:
            section_lines.append(_format_message_row(m))
        sections.append("\n".join(section_lines))
        total_unread += len(messages)

    if not sections and not errors:
        return "[0 unread across all spaces]"

    out = []
    if sections:
        out.append(f"[{total_unread} unread across {len(sections)} space(s)]")
        out.extend(sections)
    if errors:
        out.append("")
        out.append("Errors:")
        out.extend(f"  - {e}" for e in errors)
    return "\n".join(out)


class _Err:
    def __init__(self, msg: str):
        self.msg = msg


def _run(cmd: list[str], timeout: int = 30) -> _Err | dict:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return _Err(f"timed out after {timeout}s")

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return _Err(f"{AUTH_HINT} (stderr: {stderr})")
        return _Err(f"exit {result.returncode}: {stderr or '(no stderr)'}")

    text = (result.stdout or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        return _Err(f"invalid json from gws: {exc}")


def _list_spaces(gws: str, max_spaces: int) -> list[dict] | str:
    parsed = _run([
        gws, "chat", "spaces", "list",
        "--format", "json",
        "--params", json.dumps({"pageSize": max_spaces}),
    ])
    if isinstance(parsed, _Err):
        return f"Error listing spaces: {parsed.msg}"
    spaces = parsed.get("spaces") if isinstance(parsed, dict) else None
    return spaces or []


def _get_last_read(gws: str, space_name: str) -> str | _Err:
    parsed = _run([
        gws, "chat", "users", "spaces", "getSpaceReadState",
        "--format", "json",
        "--params", json.dumps({"name": f"users/me/{space_name}/spaceReadState"}),
    ])
    if isinstance(parsed, _Err):
        return parsed
    return str(parsed.get("lastReadTime") or "") if isinstance(parsed, dict) else ""


def _list_unread(
    gws: str,
    space_name: str,
    last_read: str,
    max_per_space: int,
) -> list[dict] | _Err:
    params: dict = {
        "parent": space_name,
        "pageSize": max_per_space,
        "orderBy": "createTime asc",
    }
    if last_read:
        params["filter"] = f'createTime > "{last_read}"'

    parsed = _run([
        gws, "chat", "spaces", "messages", "list",
        "--format", "json",
        "--params", json.dumps(params),
    ])
    if isinstance(parsed, _Err):
        return parsed
    if not isinstance(parsed, dict):
        return []
    messages = parsed.get("messages") or []
    return [m for m in messages if isinstance(m, dict)]


def _format_message_row(m: dict) -> str:
    name = m.get("name") or "?"
    thread = (m.get("thread") or {}).get("name") or "?"
    create_time = m.get("createTime") or "?"
    sender = (m.get("sender") or {}).get("name") or "?"
    text = m.get("text") or m.get("formattedText") or m.get("argumentText") or ""
    text = " ".join(str(text).split())
    if len(text) > SNIPPET_LIMIT:
        text = text[: SNIPPET_LIMIT - 3] + "..."
    return f"{name} | {thread} | {create_time} | {sender} | {text}"
