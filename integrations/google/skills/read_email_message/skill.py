import json
import shutil
import subprocess


GWS_MISSING = (
    "Error: `gws` CLI not installed. "
    "Install with: brew install googleworkspace-cli"
)

AUTH_HINT = "Error: `gws` is not authenticated. Run: gws auth setup"

AUTH_KEYWORDS = ("auth", "credential", "token", "login", "consent", "unauthorized")

HEADER_KEYS = ("From", "To", "Cc", "Bcc", "Subject", "Date", "Reply-To")

HEADER_LOOKUP: dict[str, tuple[str, ...]] = {
    "From": ("From", "from", "sender"),
    "To": ("To", "to"),
    "Cc": ("Cc", "cc"),
    "Bcc": ("Bcc", "bcc"),
    "Subject": ("Subject", "subject", "title"),
    "Date": ("Date", "date", "internalDate"),
    "Reply-To": ("Reply-To", "reply_to", "replyTo"),
}


def run(**input) -> str:
    msg_id = input.get("id")
    if not msg_id:
        return "Error: `id` is required."

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    cmd = [gws, "gmail", "+read", "--id", str(msg_id), "--headers", "--format", "json"]
    if input.get("html"):
        cmd.append("--html")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "Error: `gws gmail +read` timed out after 30s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    return _format(result.stdout, want_html=bool(input.get("html")))


def _format(stdout: str, want_html: bool) -> str:
    text = stdout.strip()
    if not text:
        return "(empty response from gws)"

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text

    headers = _extract_headers(parsed)
    body = _extract_body(parsed, want_html)

    lines: list[str] = []
    for key in HEADER_KEYS:
        value = headers.get(key)
        if value:
            lines.append(f"{key}: {value}")
    if lines:
        lines.append("")
    lines.append(body or "(empty body)")
    return "\n".join(lines)


def _extract_headers(parsed) -> dict:
    if not isinstance(parsed, dict):
        return {}

    nested = parsed.get("headers")
    flat: dict = {}
    if isinstance(nested, dict):
        flat.update({str(k): v for k, v in nested.items()})
    elif isinstance(nested, list):
        for item in nested:
            if isinstance(item, dict):
                name = item.get("name") or item.get("key")
                value = item.get("value")
                if name and value is not None:
                    flat[str(name)] = value

    out: dict = {}
    for canonical, variants in HEADER_LOOKUP.items():
        value = None
        for variant in variants:
            if variant in flat:
                value = flat[variant]
                break
            if variant in parsed:
                value = parsed[variant]
                break
        rendered = _render_address(value)
        if rendered:
            out[canonical] = rendered
    return out


def _render_address(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        name = value.get("name")
        email = value.get("email") or value.get("address")
        if name and email:
            return f"{name} <{email}>"
        return str(name or email or "")
    if isinstance(value, list):
        rendered = [_render_address(v) for v in value]
        return ", ".join(r for r in rendered if r)
    return str(value)


def _extract_body(parsed, want_html: bool) -> str:
    if not isinstance(parsed, dict):
        return parsed if isinstance(parsed, str) else ""
    keys = ("body_html", "html", "body", "text") if want_html else (
        "body_text", "text", "plain", "body", "content"
    )
    for key in keys:
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""
