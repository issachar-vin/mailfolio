"""Unit tests for _verify_hcaptcha — httpx calls are intercepted with respx."""

import httpx
import respx

from mailfolio.main import _HCAPTCHA_VERIFY_URL, _verify_hcaptcha


@respx.mock
async def test_returns_true_on_success() -> None:
    respx.post(_HCAPTCHA_VERIFY_URL).mock(return_value=httpx.Response(200, json={"success": True}))
    assert await _verify_hcaptcha("valid-token", "test-secret") is True


@respx.mock
async def test_returns_false_on_failure() -> None:
    respx.post(_HCAPTCHA_VERIFY_URL).mock(
        return_value=httpx.Response(
            200, json={"success": False, "error-codes": ["invalid-input-response"]}
        )
    )
    assert await _verify_hcaptcha("bad-token", "test-secret") is False


@respx.mock
async def test_returns_false_when_success_key_missing() -> None:
    respx.post(_HCAPTCHA_VERIFY_URL).mock(
        return_value=httpx.Response(200, json={"error-codes": ["missing-input-secret"]})
    )
    assert await _verify_hcaptcha("token", "bad-secret") is False


@respx.mock
async def test_posts_correct_payload() -> None:
    route = respx.post(_HCAPTCHA_VERIFY_URL).mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    await _verify_hcaptcha("my-token", "my-secret")

    assert route.called
    request = route.calls.last.request
    body = dict(pair.split("=") for pair in request.content.decode().split("&"))
    assert body["secret"] == "my-secret"
    assert body["response"] == "my-token"


@respx.mock
async def test_returns_false_on_unexpected_response_shape() -> None:
    respx.post(_HCAPTCHA_VERIFY_URL).mock(return_value=httpx.Response(200, json={}))
    assert await _verify_hcaptcha("token", "secret") is False
