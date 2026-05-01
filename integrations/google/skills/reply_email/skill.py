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
    message_id = input.get("message_id")
    body = input.get("body")
    if not message_id or body is None:
        return "Error: `message_id` and `body` are both required."

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    helper = "+reply-all" if input.get("reply_all") else "+reply"
    cmd = [
        gws, "gmail", helper,
        "--format", "json",
        "--message-id", str(message_id),
        "--body", str(body),
    ]
    if cc := input.get("cc"):
        cmd += ["--cc", cc]
    if bcc := input.get("bcc"):
        cmd += ["--bcc", bcc]
    if input.get("html"):
        cmd.append("--html")
    if input.get("draft"):
        cmd.append("--draft")
    if input.get("dry_run"):
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return "Error: `gws gmail +reply` timed out after 60s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    return _format_success(result.stdout, input, helper)


def _format_success(stdout: str, params: dict, helper: str) -> str:
    if params.get("dry_run"):
        action = "Dry-run validated"
    elif params.get("draft"):
        action = "Drafted reply"
    else:
        action = "Replied" if helper == "+reply" else "Replied-all"

    summary = f"{action}: in_reply_to={params['message_id']!r}"
    if cc := params.get("cc"):
        summary += f" cc={cc!r}"
    if bcc := params.get("bcc"):
        summary += f" bcc={bcc!r}"

    text = stdout.strip()
    if not text:
        return summary

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return f"{summary}\n\ngws output:\n{text}"

    msg_id = _find_id(parsed)
    if msg_id:
        return f"{summary}\nmessage id: {msg_id}"
    return f"{summary}\n\ngws response: {json.dumps(parsed)[:500]}"


def _find_id(obj) -> str | None:
    if isinstance(obj, dict):
        for key in ("id", "messageId", "draftId", "threadId"):
            v = obj.get(key)
            if v:
                return str(v)
        for v in obj.values():
            found = _find_id(v)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_id(item)
            if found:
                return found
    return None
