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
    max_results = int(input.get("max_results") or 50)

    gws = shutil.which("gws")
    if not gws:
        return GWS_MISSING

    params: dict = {"pageSize": max_results}
    if filter_expr := input.get("filter"):
        params["filter"] = str(filter_expr)

    cmd = [
        gws, "chat", "spaces", "list",
        "--format", "json",
        "--params", json.dumps(params),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return "Error: `gws chat spaces list` timed out after 30s."

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if any(k in stderr.lower() for k in AUTH_KEYWORDS):
            return f"{AUTH_HINT}\n\ngws stderr: {stderr}"
        return f"gws error (exit {result.returncode}): {stderr or '(no stderr)'}"

    return _format(result.stdout)


def _format(stdout: str) -> str:
    text = stdout.strip()
    if not text:
        return "[0 spaces]"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text

    spaces = parsed.get("spaces") if isinstance(parsed, dict) else None
    if not spaces:
        return "[0 spaces]"

    lines = [f"[{len(spaces)} space(s)]"]
    for s in spaces:
        if not isinstance(s, dict):
            continue
        name = s.get("name") or "?"
        space_type = s.get("spaceType") or s.get("type") or "?"
        display = s.get("displayName")
        if not display:
            if s.get("singleUserBotDm"):
                display = "(bot DM)"
            elif space_type == "DIRECT_MESSAGE":
                display = "(DM)"
            else:
                display = ""
        last_active = s.get("lastActiveTime") or "?"
        line = f"{name} | {space_type} | {display} | {last_active}"
        lines.append(line)
    return "\n".join(lines)
