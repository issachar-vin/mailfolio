from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr

from mailfolio.config import Settings
from mailfolio.mailer import GmailMailer


def _load_settings() -> Settings:
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = _load_settings()
    app.state.settings = settings
    app.state.mailer = GmailMailer(settings.gmail_user, settings.gmail_app_password)
    yield


app = FastAPI(title="mailfolio", lifespan=lifespan)


def _get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _get_mailer(request: Request) -> GmailMailer:
    return request.app.state.mailer


class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str = "Contact form submission"
    message: str


@app.post("/submit", status_code=202)
async def submit(
    form: ContactForm,
    request: Request,
    settings: Settings = Depends(_get_settings),
    mailer: GmailMailer = Depends(_get_mailer),
) -> dict[str, str]:
    origin = request.headers.get("origin", "")
    if origin not in settings.valid_origins:
        raise HTTPException(status_code=403, detail="Origin not allowed")

    body = f"Name: {form.name}\nEmail: {form.email}\n\n{form.message}"
    mailer.send(
        to=settings.mail_to,
        subject=form.subject,
        body=body,
        reply_to=form.email,
    )
    return {"status": "sent"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
