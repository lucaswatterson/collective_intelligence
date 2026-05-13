from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from harness.web.auth import (
    is_logged_in,
    login_redirect_response,
    verify_password,
)


router = APIRouter()


def attach_login_routes(templates: Jinja2Templates, get_password_hash) -> APIRouter:
    @router.get("/login", response_class=HTMLResponse)
    def login_get(request: Request) -> HTMLResponse:
        if is_logged_in(request):
            return RedirectResponse(url="/", status_code=303)
        return templates.TemplateResponse(
            request, "login.html", {"error": None}
        )

    @router.post("/login", response_class=HTMLResponse)
    def login_post(request: Request, password: str = Form(...)) -> HTMLResponse:
        if verify_password(password, get_password_hash()):
            request.session["auth"] = True
            return RedirectResponse(url="/", status_code=303)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Incorrect password."},
            status_code=401,
        )

    @router.post("/logout")
    def logout(request: Request) -> RedirectResponse:
        request.session.clear()
        return login_redirect_response()

    return router
