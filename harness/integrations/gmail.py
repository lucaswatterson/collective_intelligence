import base64
import re
from email.message import EmailMessage
from functools import lru_cache
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from harness.config import load_settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailAuthError(RuntimeError):
    pass


def get_credentials() -> Credentials:
    settings = load_settings()
    token_path = settings.gmail_token_path
    client_secrets_path = settings.gmail_client_secrets_path

    if not token_path.exists():
        raise GmailAuthError(
            f"No cached Gmail token at {token_path}. "
            f"Drop OAuth client_secrets.json into {client_secrets_path.parent} "
            f"and run: uv run scripts/gmail_auth.py"
        )

    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
        else:
            raise GmailAuthError(
                "Cached Gmail token is invalid and cannot be refreshed. "
                "Re-run: uv run scripts/gmail_auth.py"
            )
    return creds


@lru_cache(maxsize=1)
def get_service():
    return build("gmail", "v1", credentials=get_credentials(), cache_discovery=False)


def _headers(msg: dict[str, Any]) -> dict[str, str]:
    return {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}


def format_message_summary(msg: dict[str, Any]) -> str:
    h = _headers(msg)
    labels = ", ".join(msg.get("labelIds", []))
    return (
        f"id={msg.get('id')} thread={msg.get('threadId')}\n"
        f"  from:    {h.get('From', '')}\n"
        f"  to:      {h.get('To', '')}\n"
        f"  date:    {h.get('Date', '')}\n"
        f"  subject: {h.get('Subject', '')}\n"
        f"  labels:  {labels}\n"
        f"  snippet: {msg.get('snippet', '')}"
    )


def _html_to_text(html: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def decode_body(payload: dict[str, Any]) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data")
        if data:
            raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            if mime == "text/plain":
                plain_parts.append(raw)
            elif mime == "text/html":
                html_parts.append(raw)
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    if plain_parts:
        return "\n".join(plain_parts).strip()
    if html_parts:
        return _html_to_text("\n".join(html_parts))
    return ""


def format_message_full(msg: dict[str, Any]) -> str:
    h = _headers(msg)
    body = decode_body(msg.get("payload", {}))
    labels = ", ".join(msg.get("labelIds", []))
    return (
        f"id={msg.get('id')} thread={msg.get('threadId')}\n"
        f"from:    {h.get('From', '')}\n"
        f"to:      {h.get('To', '')}\n"
        f"cc:      {h.get('Cc', '')}\n"
        f"date:    {h.get('Date', '')}\n"
        f"subject: {h.get('Subject', '')}\n"
        f"labels:  {labels}\n"
        f"message-id: {h.get('Message-ID', '')}\n"
        f"\n{body}"
    )


def build_raw_message(
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    bcc: str | None = None,
    in_reply_to_header: str | None = None,
    references_header: str | None = None,
) -> str:
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    if in_reply_to_header:
        msg["In-Reply-To"] = in_reply_to_header
        msg["References"] = references_header or in_reply_to_header
    msg.set_content(body)
    return base64.urlsafe_b64encode(bytes(msg)).decode("ascii")


def lookup_message_id_header(service, gmail_message_id: str) -> str | None:
    msg = service.users().messages().get(
        userId="me", id=gmail_message_id, format="metadata",
        metadataHeaders=["Message-ID", "References"],
    ).execute()
    headers = _headers(msg)
    return headers.get("Message-ID")
