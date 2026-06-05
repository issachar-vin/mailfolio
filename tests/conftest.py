from unittest.mock import MagicMock

from mailfolio.config import Settings


def make_settings(
    *,
    valid_origins: list[str] | None = None,
    hcaptcha_secret: str | None = None,
    enable_rate_limit: bool = True,
    rate_limit: str = "1000/minute",
) -> MagicMock:
    """Return a MagicMock that quacks like Settings with sensible test defaults."""
    s = MagicMock(spec=Settings)
    s.valid_origins = valid_origins if valid_origins is not None else ["example.com"]
    s.gmail_user = "test@gmail.com"
    s.gmail_app_password = "secret"
    s.mail_to = "owner@example.com"
    s.hcaptcha_secret = hcaptcha_secret
    s.enable_rate_limit = enable_rate_limit
    s.rate_limit = rate_limit
    return s
