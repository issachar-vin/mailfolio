from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from mailfolio.main import app


@pytest.fixture
def client() -> TestClient:
    settings = MagicMock()
    settings.valid_origins = ["https://example.com"]
    settings.gmail_user = "test@gmail.com"
    settings.gmail_app_password = "secret"
    settings.mail_to = "owner@example.com"

    mailer = MagicMock()
    app.state.settings = settings
    app.state.mailer = mailer
    return TestClient(app, raise_server_exceptions=True)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_submit_valid_origin(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={"name": "Alice", "email": "alice@example.com", "message": "Hello"},
        headers={"Origin": "https://example.com"},
    )
    assert r.status_code == 202
    app.state.mailer.send.assert_called_once()


def test_submit_blocked_origin(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={"name": "Eve", "email": "eve@evil.com", "message": "Attack"},
        headers={"Origin": "https://evil.com"},
    )
    assert r.status_code == 403


def test_submit_missing_origin(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={"name": "Bot", "email": "bot@example.com", "message": "Spam"},
    )
    assert r.status_code == 403


def test_submit_invalid_email(client: TestClient) -> None:
    r = client.post(
        "/submit",
        json={"name": "Alice", "email": "not-an-email", "message": "Hello"},
        headers={"Origin": "https://example.com"},
    )
    assert r.status_code == 422
