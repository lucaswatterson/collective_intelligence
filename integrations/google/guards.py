"""Pre-flight predicates for the Google Workspace integration.

This file is a guards plugin: `scripts/install_google_workspace.py` copies it
to `entity/guards/google.py`, and the harness discovers it from there via
`harness.runtime.guards.load_guards()`. The harness expects a top-level
`GUARDS` mapping of name -> no-arg callable returning bool.

Each guard returns True to mean "go ahead and enqueue the task" and False to
mean "nothing to do, skip this fire." Errors fail open (return True) — an LLM
call is cheaper than a missed message.
"""

import json
import logging
import shutil
import subprocess
from collections.abc import Callable


log = logging.getLogger(__name__)


GWS_TIMEOUT = 15


def _gws() -> str | None:
    return shutil.which("gws")


def _run_json(cmd: list[str]) -> object | None:
    """Run `cmd`, return parsed JSON or None on any failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=GWS_TIMEOUT
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        log.warning("guard subprocess failed (%s): %s", " ".join(cmd), exc)
        return None
    if result.returncode != 0:
        log.warning(
            "guard subprocess exit %d (%s): %s",
            result.returncode, " ".join(cmd), (result.stderr or "").strip(),
        )
        return None
    text = (result.stdout or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        log.warning("guard could not parse json from %s: %s", cmd[0], exc)
        return None


def _extract_messages(parsed: object) -> list[dict]:
    """Tolerate the same shapes the read_email skill tolerates: a JSON array,
    a single object, or a wrapper dict with messages/items/results/data."""
    if isinstance(parsed, list):
        return [m for m in parsed if isinstance(m, dict)]
    if isinstance(parsed, dict):
        for key in ("messages", "items", "results", "data"):
            inner = parsed.get(key)
            if isinstance(inner, list):
                return [m for m in inner if isinstance(m, dict)]
        return [parsed] if parsed else []
    return []


def _gmail_has_unread() -> bool:
    """True if there is at least one unread message in the triage view."""
    gws = _gws()
    if not gws:
        log.warning("guard gmail_has_unread: `gws` not on PATH; failing open")
        return True

    parsed = _run_json([gws, "gmail", "+triage", "--format", "json", "--max", "1"])
    if parsed is None:
        return True  # fail-open

    messages = _extract_messages(parsed)
    return len(messages) > 0


def _gchat_has_unread() -> bool:
    """True if any Chat space has at least one message newer than its
    lastReadTime. Returns on the first unread found across spaces."""
    gws = _gws()
    if not gws:
        log.warning("guard gchat_has_unread: `gws` not on PATH; failing open")
        return True

    parsed = _run_json([
        gws, "chat", "spaces", "list",
        "--format", "json",
        "--params", json.dumps({"pageSize": 50}),
    ])
    if parsed is None:
        return True
    spaces = parsed.get("spaces") if isinstance(parsed, dict) else None
    if not spaces:
        return False

    for space in spaces:
        if not isinstance(space, dict):
            continue
        name = space.get("name")
        if not name:
            continue

        read_state = _run_json([
            gws, "chat", "users", "spaces", "getSpaceReadState",
            "--format", "json",
            "--params", json.dumps({"name": f"users/me/{name}/spaceReadState"}),
        ])
        if read_state is None:
            return True  # fail-open per-space too — don't silently miss
        last_read = (
            str(read_state.get("lastReadTime") or "")
            if isinstance(read_state, dict)
            else ""
        )

        params: dict = {"parent": name, "pageSize": 1, "orderBy": "createTime asc"}
        if last_read:
            params["filter"] = f'createTime > "{last_read}"'

        messages = _run_json([
            gws, "chat", "spaces", "messages", "list",
            "--format", "json",
            "--params", json.dumps(params),
        ])
        if messages is None:
            return True
        if isinstance(messages, dict):
            msg_list = messages.get("messages") or []
            if any(isinstance(m, dict) for m in msg_list):
                return True

    return False


GUARDS: dict[str, Callable[[], bool]] = {
    "gmail_has_unread": _gmail_has_unread,
    "gchat_has_unread": _gchat_has_unread,
}
