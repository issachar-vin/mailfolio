"""Integration tests for POST /submit."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mailfolio.main import app

_VALID_FORM = {"name": "Alice", "email": "alice@example.com", "message": "Hello"}
_VALID_HEADERS = {"Origin": "https://example.com"}


# ---------------------------------------------------------------------------
# Origin validation
# ---------------------------------------------------------------------------


def test_valid_origin_returns_202(client: TestClient) -> None:
    r = client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    assert r.status_code == 202


def test_valid_origin_sends_email(client: TestClient) -> None:
    client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    app.state.mailer.send.assert_called_once()


def test_valid_origin_response_body(client: TestClient) -> None:
    r = client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    assert r.json() == {"status": "sent"}


def test_blocked_origin_returns_403(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json=_VALID_FORM,
        headers={"Origin": "https://evil.com"},
    )
    assert r.status_code == 403


def test_missing_origin_header_returns_403(client: TestClient) -> None:
    r = client.post("/submit", json=_VALID_FORM)
    assert r.status_code == 403


def test_empty_origin_header_returns_403(client: TestClient) -> None:
    r = client.post("/submit", json=_VALID_FORM, headers={"Origin": ""})
    assert r.status_code == 403


def test_origin_with_path_is_extracted_correctly(client: TestClient) -> None:
    # Origin headers never contain paths in practice, but the extractor should
    # still match on hostname only.
    r = client.post("/submit", json=_VALID_FORM, headers={"Origin": "https://example.com/ignored"})
    assert r.status_code == 202


# ---------------------------------------------------------------------------
# Wildcard origins
# ---------------------------------------------------------------------------


def test_wildcard_matches_subdomain(wildcard_client: TestClient) -> None:
    r = wildcard_client.post(
        "/submit", json=_VALID_FORM, headers={"Origin": "https://app.example.com"}
    )
    assert r.status_code == 202


def test_wildcard_matches_deep_subdomain(wildcard_client: TestClient) -> None:
    r = wildcard_client.post(
        "/submit", json=_VALID_FORM, headers={"Origin": "https://a.b.example.com"}
    )
    assert r.status_code == 202


def test_wildcard_does_not_match_apex(wildcard_client: TestClient) -> None:
    r = wildcard_client.post("/submit", json=_VALID_FORM, headers={"Origin": "https://example.com"})
    assert r.status_code == 403


def test_wildcard_blocks_unrelated_domain(wildcard_client: TestClient) -> None:
    r = wildcard_client.post(
        "/submit",
        json={"name": "Eve", "email": "eve@evil.com", "message": "Attack"},
        headers={"Origin": "https://evil.com"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Form validation
# ---------------------------------------------------------------------------


def test_invalid_email_returns_422(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={"name": "Alice", "email": "not-an-email", "message": "Hello"},
        headers=_VALID_HEADERS,
    )
    assert r.status_code == 422


def test_missing_name_returns_422(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={"email": "alice@example.com", "message": "Hello"},
        headers=_VALID_HEADERS,
    )
    assert r.status_code == 422


def test_missing_message_returns_422(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={"name": "Alice", "email": "alice@example.com"},
        headers=_VALID_HEADERS,
    )
    assert r.status_code == 422


def test_custom_subject_is_forwarded(client: TestClient) -> None:
    client.post(
        "/submit",
        json={**_VALID_FORM, "subject": "Custom Subject"},
        headers=_VALID_HEADERS,
    )
    call_kwargs = app.state.mailer.send.call_args.kwargs
    assert call_kwargs["subject"] == "Custom Subject"


def test_default_subject_is_used_when_omitted(client: TestClient) -> None:
    client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    call_kwargs = app.state.mailer.send.call_args.kwargs
    assert call_kwargs["subject"] == "Contact form submission"


def test_reply_to_is_set_to_sender_email(client: TestClient) -> None:
    client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    call_kwargs = app.state.mailer.send.call_args.kwargs
    assert call_kwargs["reply_to"] == "alice@example.com"


def test_email_body_contains_name_and_message(client: TestClient) -> None:
    client.post(
        "/submit",
        json={"name": "Bob", "email": "bob@example.com", "message": "Hi there"},
        headers=_VALID_HEADERS,
    )
    call_kwargs = app.state.mailer.send.call_args.kwargs
    assert "Bob" in call_kwargs["body"]
    assert "Hi there" in call_kwargs["body"]


# ---------------------------------------------------------------------------
# hCaptcha — disabled
# ---------------------------------------------------------------------------


def test_hcaptcha_disabled_accepts_without_token(client: TestClient) -> None:
    r = client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    assert r.status_code == 202


def test_hcaptcha_disabled_ignores_token_if_provided(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={**_VALID_FORM, "hcaptcha_token": "ignored"},
        headers=_VALID_HEADERS,
    )
    assert r.status_code == 202


# ---------------------------------------------------------------------------
# hCaptcha — enabled
# ---------------------------------------------------------------------------


def test_hcaptcha_enabled_missing_token_returns_422(hcaptcha_client: TestClient) -> None:
    r = hcaptcha_client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    assert r.status_code == 422
    assert "hCaptcha" in r.json()["detail"]


def test_hcaptcha_enabled_invalid_token_returns_403(hcaptcha_client: TestClient) -> None:
    with patch("mailfolio.main._verify_hcaptcha", new=AsyncMock(return_value=False)):
        r = hcaptcha_client.post(
            "/submit",
            json={**_VALID_FORM, "hcaptcha_token": "bad-token"},
            headers=_VALID_HEADERS,
        )
    assert r.status_code == 403
    assert "hCaptcha" in r.json()["detail"]


def test_hcaptcha_enabled_valid_token_returns_202(hcaptcha_client: TestClient) -> None:
    with patch("mailfolio.main._verify_hcaptcha", new=AsyncMock(return_value=True)):
        r = hcaptcha_client.post(
            "/submit",
            json={**_VALID_FORM, "hcaptcha_token": "good-token"},
            headers=_VALID_HEADERS,
        )
    assert r.status_code == 202


def test_hcaptcha_origin_checked_before_captcha(hcaptcha_client: TestClient) -> None:
    # A blocked origin should 403 before we even attempt captcha verification.
    with patch("mailfolio.main._verify_hcaptcha", new=AsyncMock()) as mock_verify:
        r = hcaptcha_client.post(
            "/submit",
            json={**_VALID_FORM, "hcaptcha_token": "token"},
            headers={"Origin": "https://evil.com"},
        )
    assert r.status_code == 403
    mock_verify.assert_not_called()


def test_hcaptcha_enabled_empty_string_token_returns_422(hcaptcha_client: TestClient) -> None:
    # Empty string is falsy — treated the same as no token provided.
    r = hcaptcha_client.post(
        "/submit",
        json={**_VALID_FORM, "hcaptcha_token": ""},
        headers=_VALID_HEADERS,
    )
    assert r.status_code == 422


@pytest.mark.parametrize("token", [" ", "\x00", "garbage"])
def test_hcaptcha_enabled_truthy_invalid_token_returns_403(
    hcaptcha_client: TestClient, token: str
) -> None:
    with patch("mailfolio.main._verify_hcaptcha", new=AsyncMock(return_value=False)):
        r = hcaptcha_client.post(
            "/submit",
            json={**_VALID_FORM, "hcaptcha_token": token},
            headers=_VALID_HEADERS,
        )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_rate_limit_first_request_succeeds(rate_limit_client: TestClient) -> None:
    r = rate_limit_client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    assert r.status_code == 202


def test_rate_limit_second_request_is_blocked(rate_limit_client: TestClient) -> None:
    rate_limit_client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    r = rate_limit_client.post("/submit", json=_VALID_FORM, headers=_VALID_HEADERS)
    assert r.status_code == 429
