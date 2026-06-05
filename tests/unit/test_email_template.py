"""Unit tests for build_contact_email."""

from email.mime.multipart import MIMEMultipart

import pytest

from mailfolio.email_template import build_contact_email


@pytest.fixture
def msg() -> MIMEMultipart:
    return build_contact_email(
        name="Alice",
        email="alice@example.com",
        subject="Hello there",
        message="Just saying hi.",
    )


def _part(msg: MIMEMultipart, content_type: str) -> str:
    for part in msg.walk():
        if part.get_content_type() == content_type:
            payload = part.get_payload(decode=True)
            assert payload is not None
            return payload.decode()
    pytest.fail(f"No {content_type} part found")


# ---------------------------------------------------------------------------
# Headers
# ---------------------------------------------------------------------------


def test_subject_header(msg: MIMEMultipart) -> None:
    assert msg["Subject"] == "Hello there"


def test_reply_to_header(msg: MIMEMultipart) -> None:
    assert msg["Reply-To"] == "alice@example.com"


def test_from_and_to_not_set(msg: MIMEMultipart) -> None:
    # From/To are set by GmailMailer.send, not by the template builder.
    assert msg["From"] is None
    assert msg["To"] is None


# ---------------------------------------------------------------------------
# Plain text part
# ---------------------------------------------------------------------------


def test_plain_part_exists(msg: MIMEMultipart) -> None:
    _part(msg, "text/plain")


def test_plain_contains_name(msg: MIMEMultipart) -> None:
    assert "Alice" in _part(msg, "text/plain")


def test_plain_contains_email(msg: MIMEMultipart) -> None:
    assert "alice@example.com" in _part(msg, "text/plain")


def test_plain_contains_message(msg: MIMEMultipart) -> None:
    assert "Just saying hi." in _part(msg, "text/plain")


# ---------------------------------------------------------------------------
# HTML part
# ---------------------------------------------------------------------------


def test_html_part_exists(msg: MIMEMultipart) -> None:
    _part(msg, "text/html")


def test_html_contains_name(msg: MIMEMultipart) -> None:
    assert "Alice" in _part(msg, "text/html")


def test_html_contains_email(msg: MIMEMultipart) -> None:
    assert "alice@example.com" in _part(msg, "text/html")


def test_html_contains_subject(msg: MIMEMultipart) -> None:
    assert "Hello there" in _part(msg, "text/html")


def test_html_contains_message(msg: MIMEMultipart) -> None:
    assert "Just saying hi." in _part(msg, "text/html")


def test_html_has_reply_mailto(msg: MIMEMultipart) -> None:
    assert "mailto:" in _part(msg, "text/html")


# ---------------------------------------------------------------------------
# HTML escaping
# ---------------------------------------------------------------------------


def test_html_escapes_name() -> None:
    m = build_contact_email(
        name="<script>alert(1)</script>",
        email="x@example.com",
        subject="s",
        message="m",
    )
    body = _part(m, "text/html")
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


def test_html_escapes_message() -> None:
    m = build_contact_email(
        name="Bob",
        email="bob@example.com",
        subject="s",
        message="<b>bold</b> & more",
    )
    body = _part(m, "text/html")
    assert "<b>" not in body
    assert "&lt;b&gt;" in body
    assert "&amp;" in body
