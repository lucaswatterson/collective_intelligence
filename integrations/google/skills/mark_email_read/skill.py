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
    raw = input.get("ids")
    if raw is None or raw == "" or raw == []:
        return "Error: `ids` is required (string or list of strings)."

    if isinstance(raw, str):
        ids = [raw]
    elif isinstance(raw, list):
        ids = [str(x) for x in raw if x]
    else:
        return f"Error: `ids` must be a string or list, got {type(raw).__name__}."

    if not ids:
        return "Error: `ids` is empty."

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    if len(ids) == 1:
        cmd = [
            gws, "gmail", "users", "messages", "modify",
            "--format", "json",
            "--params", json.dumps({"userId": "me", "id": ids[0]}),
            "--json", json.dumps({"removeLabelIds": ["UNREAD"]}),
        ]
    else:
        cmd = [
            gws, "gmail", "users", "messages", "batchModify",
            "--format", "json",
            "--params", json.dumps({"userId": "me"}),
            "--json", json.dumps({"ids": ids, "removeLabelIds": ["UNREAD"]}),
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "Error: `gws` mark-read call timed out after 30s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    return f"Marked {len(ids)} message(s) read: {', '.join(ids)}"
