import secrets
import sys

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Request, status
from fastapi.responses import RedirectResponse

from harness.config import Settings


_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def resolve_session_secret(settings: Settings) -> str:
    if settings.web_session_secret:
        return settings.web_session_secret
    return secrets.token_urlsafe(32)


def is_logged_in(request: Request) -> bool:
    return bool(request.session.get("auth"))


def login_redirect_response() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


def _cli() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "hash":
        print(hash_password(sys.argv[2]))
        return
    print("usage: python -m harness.web.auth hash <password>", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    _cli()
