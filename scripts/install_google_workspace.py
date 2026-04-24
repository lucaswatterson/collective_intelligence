"""Install / uninstall Google Workspace MCP integration.

Per product, runs an OAuth 2.0 Desktop-app loopback flow against the user's
GCP project, captures a refresh token, and writes credentials to
`harness/secrets/google/{product}.json`. Stdlib only — no new deps.

GCP preconditions (printed on run):
  - Enrolled in the Google Workspace Developer Preview Program.
  - A GCP project with the product's APIs enabled plus the matching
    `*mcp.googleapis.com` service.
  - An OAuth 2.0 Client ID of type **Desktop app**. Loopback redirects
    (http://localhost:PORT) do not need a whitelist entry for Desktop clients.

Usage:
  uv run scripts/install_google_workspace.py               # install default products
  uv run scripts/install_google_workspace.py --products gmail,calendar
  uv run scripts/install_google_workspace.py --list
  uv run scripts/install_google_workspace.py --uninstall gmail
  uv run scripts/install_google_workspace.py --uninstall all
"""

import argparse
import getpass
import http.server
import json
import secrets
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.config import load_settings
from harness.integrations.google import PRODUCTS, TOKEN_URI


AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
REVOKE_URI = "https://oauth2.googleapis.com/revoke"
DEFAULT_PRODUCTS = ("gmail", "calendar", "drive", "people")


def _print_gcp_checklist() -> None:
    print("=" * 60)
    print("Google Workspace MCP — setup checklist")
    print("=" * 60)
    print("Before running this installer you need:")
    print("  1. Enrollment in the Google Workspace Developer Preview Program:")
    print("     https://developers.google.com/workspace/preview")
    print("  2. A GCP project with these services enabled:")
    for product in DEFAULT_PRODUCTS:
        services = ", ".join(PRODUCTS[product]["gcp_services"])
        print(f"       {product}: {services}")
    print("  3. An OAuth 2.0 Client ID of type **Web application**.")
    print("     Add http://127.0.0.1:8765 to the authorized redirect URIs.")
    print("     (Google's MCP servers require Web-type clients for Claude, NOT Desktop.)")
    print("  4. The OAuth consent screen configured with the requested scopes.")
    print("=" * 60)
    print()


class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    captured: dict[str, str] = {}

    def do_GET(self) -> None:
        sys.stderr.write(f"  [callback] GET {self.path}\n")
        sys.stderr.flush()
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if not any(k in params for k in ("code", "state", "error")):
            self.send_response(204)
            self.end_headers()
            return
        for key in ("code", "state", "error"):
            if key in params:
                _OAuthCallbackHandler.captured[key] = params[key][0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        body = (
            b"<html><body><h2>You can close this tab.</h2>"
            b"<p>Authorization received; return to the installer.</p>"
            b"</body></html>"
        )
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class _ReusableHTTPServer(http.server.HTTPServer):
    allow_reuse_address = True


def _run_oauth_flow(
    *,
    client_id: str,
    client_secret: str,
    scopes: list[str],
    port: int,
) -> dict[str, str]:
    state = secrets.token_urlsafe(24)
    redirect_uri = f"http://127.0.0.1:{port}"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    auth_url = f"{AUTH_URI}?{urllib.parse.urlencode(params)}"

    # allow_reuse_address lets us rebind across a TIME_WAIT socket from a prior
    # flow in THIS process — but it also lets us bind on top of a zombie server
    # in another process, which would silently steal redirects. Probe first.
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.settimeout(0.5)
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(
                f"Something is already listening on 127.0.0.1:{port}. "
                f"Find it with: lsof -nP -iTCP:{port} -sTCP:LISTEN  — then kill that PID."
            )
    finally:
        probe.close()

    _OAuthCallbackHandler.captured = {}
    server = _ReusableHTTPServer(("127.0.0.1", port), _OAuthCallbackHandler)
    server.timeout = 1.0  # handle_request() returns after 1s if no request — lets SIGINT land cleanly

    try:
        print(f"\nOpening browser for consent. If it doesn't open, visit:\n  {auth_url}\n", flush=True)
        webbrowser.open(auth_url)

        print(f"Waiting for redirect on {redirect_uri} ... (Ctrl+C to cancel)", flush=True)
        waited = 0
        while "code" not in _OAuthCallbackHandler.captured and "error" not in _OAuthCallbackHandler.captured:
            server.handle_request()  # blocks up to server.timeout, then re-checks
            waited += 1
            if waited and waited % 30 == 0:
                print(f"  ...still waiting ({waited}s). Expected redirect: {redirect_uri}", flush=True)
    finally:
        server.server_close()
    print("  [flow] callback server closed.", flush=True)

    captured = _OAuthCallbackHandler.captured
    if "error" in captured:
        raise RuntimeError(f"OAuth error: {captured['error']}")
    if captured.get("state") != state:
        raise RuntimeError("OAuth state mismatch — aborting.")
    code = captured["code"]
    print("  [flow] exchanging code for refresh_token...", flush=True)

    body = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URI,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Token exchange failed: HTTP {exc.code}\n{body}") from exc
    print("  [flow] refresh_token received.", flush=True)

    if "refresh_token" not in payload:
        raise RuntimeError(
            "Google did not return a refresh_token. Re-run with `prompt=consent` "
            "and verify your OAuth client is type 'Desktop app'."
        )
    return payload


def _install(products: list[str], port: int, client_id: str | None, client_secret: str | None) -> None:
    settings = load_settings()
    secrets_dir = settings.google_secrets_dir
    secrets_dir.mkdir(parents=True, exist_ok=True)

    if not client_id:
        client_id = input("OAuth Client ID: ").strip()
    if not client_secret:
        client_secret = getpass.getpass("OAuth Client Secret: ").strip()
    if not client_id or not client_secret:
        raise SystemExit("client_id and client_secret are required.")

    for product in products:
        if product not in PRODUCTS:
            print(f"Skipping unknown product: {product}")
            continue

        print(f"\n--- {product} ---")
        scopes = PRODUCTS[product]["scopes"]
        print("Requesting scopes:")
        for s in scopes:
            print(f"  {s}")

        payload = _run_oauth_flow(
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
            port=port,
        )
        creds = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": payload["refresh_token"],
            "scopes": scopes,
            "token_uri": TOKEN_URI,
        }
        out = secrets_dir / f"{product}.json"
        out.write_text(json.dumps(creds, indent=2), encoding="utf-8")
        out.chmod(0o600)
        rel = out.relative_to(settings.repo_root)
        print(f"Wrote {rel}")


def _uninstall(products: list[str]) -> None:
    settings = load_settings()
    secrets_dir = settings.google_secrets_dir
    if not secrets_dir.exists():
        print("Nothing installed.")
        return

    if products == ["all"]:
        products = [p.stem for p in secrets_dir.glob("*.json")]

    for product in products:
        path = secrets_dir / f"{product}.json"
        if not path.exists():
            print(f"{product}: not installed")
            continue

        try:
            creds = json.loads(path.read_text(encoding="utf-8"))
            body = urllib.parse.urlencode({"token": creds["refresh_token"]}).encode("utf-8")
            req = urllib.request.Request(
                REVOKE_URI,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
            print(f"{product}: revoked (HTTP {status})")
        except Exception as exc:
            print(f"{product}: revoke failed ({exc}); deleting credential file anyway")

        path.unlink()
        print(f"{product}: removed {path.relative_to(settings.repo_root)}")


def _list() -> None:
    settings = load_settings()
    secrets_dir = settings.google_secrets_dir
    print(f"Credentials dir: {secrets_dir.relative_to(settings.repo_root)}/")
    if not secrets_dir.exists() or not any(secrets_dir.glob("*.json")):
        print("  (no products installed)")
        return

    for path in sorted(secrets_dir.glob("*.json")):
        product = path.stem
        marker = "" if product in PRODUCTS else "  [UNKNOWN]"
        print(f"  {product}{marker}")
        if product in PRODUCTS:
            for scope in PRODUCTS[product]["scopes"]:
                print(f"      {scope}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--products",
        default=",".join(DEFAULT_PRODUCTS),
        help=f"Comma-separated product list. Default: {','.join(DEFAULT_PRODUCTS)}",
    )
    parser.add_argument("--client-id", default=None)
    parser.add_argument("--client-secret", default=None)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--list", action="store_true", dest="list_only")
    parser.add_argument(
        "--uninstall",
        nargs="?",
        const="all",
        default=None,
        help="Revoke + delete creds for comma-separated products, or 'all'.",
    )
    args = parser.parse_args()

    if args.list_only:
        _list()
        return

    if args.uninstall is not None:
        products = [p.strip() for p in args.uninstall.split(",") if p.strip()]
        _uninstall(products or ["all"])
        return

    _print_gcp_checklist()
    products = [p.strip() for p in args.products.split(",") if p.strip()]
    _install(products, args.port, args.client_id, args.client_secret)


if __name__ == "__main__":
    main()
