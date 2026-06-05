import fnmatch
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from mailfolio.config import Settings
from mailfolio.email_template import build_contact_email
from mailfolio.mailer import GmailMailer, Mailer

_HCAPTCHA_VERIFY_URL = "https://api.hcaptcha.com/siteverify"

limiter = Limiter(key_func=get_remote_address)


def _load_settings() -> Settings:
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = _load_settings()
    app.state.settings = settings
    app.state.mailer = GmailMailer(settings.gmail_user, settings.gmail_app_password)
    yield


app = FastAPI(title="mailfolio", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")
    allowed = bool(origin) and _is_allowed(origin, request.app.state.settings.valid_origins)

    if request.method == "OPTIONS":
        if allowed:
            return Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Max-Age": "86400",
                },
            )
        return Response(status_code=403)

    response = await call_next(request)
    if allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
    return response


def _rate_limit(key: str) -> str:
    return app.state.settings.rate_limit


def _is_rate_limit_disabled() -> bool:
    return not app.state.settings.enable_rate_limit


def _get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _get_mailer(request: Request) -> Mailer:
    return request.app.state.mailer


def _require_allowed_origin(
    request: Request,
    settings: Settings = Depends(_get_settings),
) -> None:
    origin = request.headers.get("origin", "")
    if not _is_allowed(origin, settings.valid_origins):
        raise HTTPException(status_code=403, detail="Origin not allowed")


def _origin_hostname(origin: str) -> str:
    # urlparse extracts netloc from a full URL ("https://example.com" → "example.com").
    # A bare hostname with no scheme is returned unchanged.
    netloc = urlparse(origin).netloc
    return netloc if netloc else origin


def _is_allowed(origin: str, valid_origins: list[str]) -> bool:
    # valid_origins holds bare hostnames or fnmatch patterns (e.g. "*.example.com").
    # fnmatch "*" crosses dots, so "*.example.com" also matches "deep.sub.example.com".
    # Add more-specific patterns to restrict further.
    hostname = _origin_hostname(origin)
    return any(fnmatch.fnmatch(hostname, pattern) for pattern in valid_origins)


async def _verify_hcaptcha(token: str, secret: str) -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _HCAPTCHA_VERIFY_URL,
            data={"secret": secret, "response": token},
        )
        return bool(resp.json().get("success", False))


class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str = "Contact form submission"
    message: str
    # Required when hCaptcha is enabled (HCAPTCHA_SECRET set in env). Ignored otherwise.
    hcaptcha_token: str | None = None


@app.post("/submit", status_code=202)
@limiter.limit(_rate_limit, exempt_when=_is_rate_limit_disabled)
async def submit(
    request: Request,
    form: ContactForm,
    settings: Settings = Depends(_get_settings),
    mailer: Mailer = Depends(_get_mailer),
    _: None = Depends(_require_allowed_origin),
) -> dict[str, str]:
    if settings.hcaptcha_secret:
        if not form.hcaptcha_token:
            raise HTTPException(status_code=422, detail="hCaptcha token required")
        if not await _verify_hcaptcha(form.hcaptcha_token, settings.hcaptcha_secret):
            raise HTTPException(status_code=403, detail="hCaptcha verification failed")

    msg = build_contact_email(form.name, form.email, form.subject, form.message)
    mailer.send(to=settings.mail_to, msg=msg)
    return {"status": "sent"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
