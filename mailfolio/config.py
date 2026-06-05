from pydantic import field_validator
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
    mail_to: str

    @field_validator("valid_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        values = [o.strip() for o in v.split(",") if o.strip()] if isinstance(v, str) else list(v)
        return [_strip_scheme(o) for o in values]
