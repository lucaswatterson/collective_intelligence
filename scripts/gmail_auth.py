"""One-time OAuth bootstrap for the Gmail integration.

Usage:
    1. Create a Google Cloud project, enable the Gmail API, and create
       an OAuth 2.0 Client ID of type "Desktop app".
    2. Download the client secrets JSON and save it to:
           harness/secrets/gmail/client_secrets.json
    3. Run:
           uv run scripts/gmail_auth.py
       A browser window will open for consent; on completion a token is
       cached to harness/secrets/gmail/token.json.
"""

import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from harness.config import load_settings
from harness.integrations.gmail import SCOPES


def main() -> int:
    settings = load_settings()
    client_secrets = settings.gmail_client_secrets_path
    token_path = settings.gmail_token_path

    if not client_secrets.exists():
        print(f"ERROR: missing {client_secrets}", file=sys.stderr)
        print(
            "Create an OAuth Desktop client in Google Cloud Console, download\n"
            "its client_secrets.json, and place it at the path above.",
            file=sys.stderr,
        )
        return 1

    token_path.parent.mkdir(parents=True, exist_ok=True)

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json())
    print(f"Cached Gmail credentials to {token_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
