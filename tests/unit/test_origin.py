"""Unit tests for origin validation helpers in main.py."""

import pytest

from mailfolio.main import _is_allowed, _origin_hostname


class TestOriginHostname:
    def test_extracts_https_netloc(self) -> None:
        assert _origin_hostname("https://example.com") == "example.com"

    def test_extracts_http_netloc(self) -> None:
        assert _origin_hostname("http://example.com") == "example.com"

    def test_bare_hostname_unchanged(self) -> None:
        assert _origin_hostname("example.com") == "example.com"

    def test_preserves_port(self) -> None:
        assert _origin_hostname("https://example.com:8080") == "example.com:8080"

    def test_strips_path(self) -> None:
        assert _origin_hostname("https://example.com/some/path") == "example.com"

    def test_empty_string(self) -> None:
        assert _origin_hostname("") == ""

    def test_subdomain(self) -> None:
        assert _origin_hostname("https://app.example.com") == "app.example.com"


class TestIsAllowed:
    def test_exact_match(self) -> None:
        assert _is_allowed("https://example.com", ["example.com"]) is True

    def test_exact_no_match(self) -> None:
        assert _is_allowed("https://evil.com", ["example.com"]) is False

    def test_wildcard_subdomain(self) -> None:
        assert _is_allowed("https://app.example.com", ["*.example.com"]) is True

    def test_wildcard_deep_subdomain(self) -> None:
        # fnmatch * crosses dots — document and assert the actual behaviour.
        assert _is_allowed("https://a.b.example.com", ["*.example.com"]) is True

    def test_wildcard_no_match_unrelated(self) -> None:
        assert _is_allowed("https://evil.com", ["*.example.com"]) is False

    def test_wildcard_does_not_match_bare_apex(self) -> None:
        # "*.example.com" should not match "example.com" itself.
        assert _is_allowed("https://example.com", ["*.example.com"]) is False

    def test_multiple_patterns_first_matches(self) -> None:
        assert _is_allowed("https://example.com", ["example.com", "other.com"]) is True

    def test_multiple_patterns_second_matches(self) -> None:
        assert _is_allowed("https://other.com", ["example.com", "other.com"]) is True

    def test_multiple_patterns_none_match(self) -> None:
        assert _is_allowed("https://evil.com", ["example.com", "other.com"]) is False

    def test_empty_origin_blocked(self) -> None:
        assert _is_allowed("", ["example.com"]) is False

    def test_empty_allowlist_blocks_all(self) -> None:
        assert _is_allowed("https://example.com", []) is False

    @pytest.mark.parametrize(
        "origin, patterns, expected",
        [
            ("https://example.com", ["example.com"], True),
            ("https://sub.example.com", ["*.example.com"], True),
            ("https://evil.com", ["example.com", "*.safe.com"], False),
            ("https://x.safe.com", ["example.com", "*.safe.com"], True),
        ],
    )
    def test_parametrized_cases(self, origin: str, patterns: list[str], expected: bool) -> None:
        assert _is_allowed(origin, patterns) is expected
