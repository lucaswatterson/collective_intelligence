"""Google Workspace Remote MCP integration — opt-in.

Credential files live at `harness/secrets/google/{product}.json` and are written
by `scripts/install_google_workspace.py`. If the directory is empty, this module
returns empty lists and the entity runs with no Google tools — fully inert.

Each credential file stores `{client_id, client_secret, refresh_token, scopes,
token_uri}`. Access tokens are minted fresh per tool loop rather than cached to
disk — avoids TUI/worker coherency bugs and a ~1hr stale-token failure mode.
If Google rotates the `refresh_token` on refresh, we rewrite the file under an
`fcntl.flock` so the two entities don't clobber each other.
"""

import fcntl
import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


log = logging.getLogger(__name__)


# URL, OAuth scopes, and GCP services to enable per product. The installer
# prints `gcp_services` so the user knows which APIs to turn on. Note People
# does not follow the `{product}mcp.googleapis.com` pattern.
#
# To later lock down tools exposed to the model (e.g., Gmail read-only),
# add `"allowed_tools": [...]` here and merge it into the toolset entry below.
PRODUCTS: dict[str, dict[str, Any]] = {
    "gmail": {
        "url": "https://gmailmcp.googleapis.com/mcp/v1",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
        ],
        "gcp_services": ["gmail.googleapis.com", "gmailmcp.googleapis.com"],
    },
    "calendar": {
        "url": "https://calendarmcp.googleapis.com/mcp/v1",
        "scopes": [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events.readonly",
            "https://www.googleapis.com/auth/calendar.freebusy",
        ],
        "gcp_services": ["calendar-json.googleapis.com", "calendarmcp.googleapis.com"],
    },
    "drive": {
        "url": "https://drivemcp.googleapis.com/mcp/v1",
        "scopes": [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.file",
        ],
        "gcp_services": ["drive.googleapis.com", "drivemcp.googleapis.com"],
    },
    "people": {
        "url": "https://people.googleapis.com/mcp/v1",
        "scopes": [
            "https://www.googleapis.com/auth/contacts.readonly",
            "https://www.googleapis.com/auth/directory.readonly",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        "gcp_services": ["people.googleapis.com"],
    },
}


TOKEN_URI = "https://oauth2.googleapis.com/token"


def _refresh_access_token(creds_path: Path) -> str:
    """Mint a fresh access token from the stored refresh token.

    If Google returns a rotated `refresh_token`, persist it back to disk under
    an flock so the TUI and worker processes don't race.
    """
    creds = json.loads(creds_path.read_text(encoding="utf-8"))

    body = urllib.parse.urlencode(
        {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        creds.get("token_uri", TOKEN_URI),
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    access_token = payload["access_token"]
    rotated = payload.get("refresh_token")
    if rotated and rotated != creds["refresh_token"]:
        _rewrite_refresh_token(creds_path, rotated)

    return access_token


def _rewrite_refresh_token(creds_path: Path, new_refresh_token: str) -> None:
    with creds_path.open("r+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.seek(0)
            current = json.loads(fh.read() or "{}")
            current["refresh_token"] = new_refresh_token
            fh.seek(0)
            fh.truncate()
            fh.write(json.dumps(current, indent=2))
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def build_google_mcp_servers(
    secrets_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build the (mcp_servers, mcp_toolsets) pair for the Messages API.

    Both lists are empty if no credential files exist — the feature is
    fully opt-in via the presence of JSON files in `secrets_dir`.
    """
    if not secrets_dir.exists():
        return [], []

    mcp_servers: list[dict[str, Any]] = []
    mcp_toolsets: list[dict[str, Any]] = []

    for creds_path in sorted(secrets_dir.glob("*.json")):
        product = creds_path.stem
        if product not in PRODUCTS:
            log.warning("Skipping unknown Google product creds file: %s", creds_path)
            continue
        try:
            token = _refresh_access_token(creds_path)
        except Exception:
            log.exception("Failed to refresh access token for %s", product)
            continue

        name = f"google_{product}"
        mcp_servers.append(
            {
                "type": "url",
                "url": PRODUCTS[product]["url"],
                "name": name,
                "authorization_token": token,
            }
        )
        mcp_toolsets.append({"type": "mcp_toolset", "mcp_server_name": name})

    return mcp_servers, mcp_toolsets
