import json
import shutil
import subprocess
from datetime import datetime, timezone


GWS_MISSING = (
    "Error: `gws` CLI not installed. "
    "Install with: brew install googleworkspace-cli"
)

AUTH_HINT = "Error: `gws` is not authenticated. Run: gws auth setup"

AUTH_KEYWORDS = ("auth", "credential", "token", "login", "consent", "unauthorized")


def run(**input) -> str:
    space = input.get("space")
    if not space:
        return "Error: `space` is required (e.g. 'spaces/AAAAxxxx')."

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    last_read = input.get("last_read_time") or _now_rfc3339()

    cmd = [
        gws, "chat", "users", "spaces", "updateSpaceReadState",
        "--format", "json",
        "--params", json.dumps({
            "name": f"users/me/{space}/spaceReadState",
            "updateMask": "lastReadTime",
        }),
        "--json", json.dumps({"lastReadTime": str(last_read)}),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "Error: `gws chat users spaces updateSpaceReadState` timed out after 30s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    return f"Marked {space} read up to {last_read}."


def _now_rfc3339() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
