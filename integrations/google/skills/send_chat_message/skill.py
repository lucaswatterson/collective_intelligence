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
    space = input.get("space")
    text = input.get("text")
    if not space or text is None:
        return "Error: `space` and `text` are both required."

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    cmd = [
        gws, "chat", "+send",
        "--format", "json",
        "--space", str(space),
        "--text", str(text),
    ]
    if input.get("dry_run"):
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "Error: `gws chat +send` timed out after 30s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    return _format_success(result.stdout, space, dry_run=bool(input.get("dry_run")))


def _format_success(stdout: str, space: str, *, dry_run: bool) -> str:
    action = "Dry-run validated" if dry_run else "Sent"
    summary = f"{action}: space={space!r}"

    text = stdout.strip()
    if not text:
        return summary
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return f"{summary}\n\ngws output:\n{text}"

    if dry_run:
        return summary
    if isinstance(parsed, dict):
        msg_name = parsed.get("name")
        if msg_name:
            return f"{summary}\nmessage: {msg_name}"
    return f"{summary}\n\ngws response: {json.dumps(parsed)[:500]}"
