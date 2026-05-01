import json
import shutil
import subprocess


GWS_MISSING = (
    "Error: `gws` CLI not installed. "
    "Install with: brew install googleworkspace-cli"
)

AUTH_HINT = "Error: `gws` is not authenticated. Run: gws auth setup"

AUTH_KEYWORDS = ("auth", "credential", "token", "login", "consent", "unauthorized")


def run(**input) -> str:
    name = input.get("name")
    if not name:
        return "Error: `name` is required (e.g. 'spaces/AAAA/messages/YYY.YYY')."

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    cmd = [
        gws, "chat", "spaces", "messages", "get",
        "--format", "json",
        "--params", json.dumps({"name": str(name)}),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "Error: `gws chat spaces messages get` timed out after 30s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    return _format(result.stdout)


def _format(stdout: str) -> str:
    text = stdout.strip()
    if not text:
        return "(empty response from gws)"

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text

    if not isinstance(parsed, dict):
        return text

    name = parsed.get("name") or "?"
    space = (parsed.get("space") or {}).get("name") or "?"
    thread = (parsed.get("thread") or {}).get("name") or "?"
    sender = (parsed.get("sender") or {}).get("name") or "?"
    sender_type = (parsed.get("sender") or {}).get("type") or ""
    create_time = parsed.get("createTime") or "?"
    last_update = parsed.get("lastUpdateTime") or ""
    body = (
        parsed.get("formattedText")
        or parsed.get("text")
        or parsed.get("argumentText")
        or ""
    )

    lines = [
        f"Name: {name}",
        f"Space: {space}",
        f"Thread: {thread}",
        f"Sender: {sender}" + (f" ({sender_type})" if sender_type else ""),
        f"Created: {create_time}",
    ]
    if last_update and last_update != create_time:
        lines.append(f"Updated: {last_update}")

    attachments = parsed.get("attachment") or parsed.get("attachments")
    if attachments:
        lines.append(f"Attachments: {len(attachments)}")

    lines.append("")
    lines.append(body or "(empty body)")
    return "\n".join(lines)
