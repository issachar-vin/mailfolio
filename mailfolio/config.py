from typing import Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _strip_scheme(value: str) -> str:
    # Normalise to a bare hostname/pattern so comparison is scheme-agnostic.
    for scheme in ("https://", "http://"):
        if value.startswith(scheme):
            return value[len(scheme) :]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Comma-separated bare hostnames or fnmatch wildcard patterns.
    # Example: "example.com,*.staging.example.com"
    # Schemes (https://) are stripped on load if accidentally included.
    valid_origins: list[str]
    gmail_user: str
    gmail_app_password: str
    # Defaults to gmail_user when omitted.
    mail_to: str | None = None
    # hCaptcha secret key. When set, /submit requires a valid hcaptcha_token in
    # the request body and verifies it against the hCaptcha siteverify API.
    # Omit to disable hCaptcha entirely.
    hcaptcha_secret: str | None = None
    # limits-style rate limit string applied per IP to POST /submit.
    # Examples: "1/minute", "10/hour", "5/second"
    rate_limit: str = "1/minute"

    @model_validator(mode="after")
    def _default_mail_to(self) -> Self:
        if not self.mail_to:
            self.mail_to = self.gmail_user
        return self

    @field_validator("valid_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        values = [o.strip() for o in v.split(",") if o.strip()] if isinstance(v, str) else list(v)
        return [_strip_scheme(o) for o in values]
