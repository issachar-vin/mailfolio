from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from mailfolio.main import app, limiter
from tests.conftest import make_settings


@pytest.fixture
def client() -> TestClient:
    app.state.settings = make_settings()
    app.state.mailer = MagicMock()
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def hcaptcha_client() -> TestClient:
    app.state.settings = make_settings(hcaptcha_secret="test-secret")
    app.state.mailer = MagicMock()
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def wildcard_client() -> TestClient:
    app.state.settings = make_settings(valid_origins=["*.example.com"])
    app.state.mailer = MagicMock()
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def rate_limit_client() -> TestClient:
    limiter._storage.reset()
    app.state.settings = make_settings(rate_limit="1/minute")
    app.state.mailer = MagicMock()
    return TestClient(app, raise_server_exceptions=True)
