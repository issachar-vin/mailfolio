"""Unit tests for config.py — _strip_scheme and the parse_origins validator."""

import pytest

from mailfolio.config import Settings, _strip_scheme


class TestStripScheme:
    def test_strips_https(self) -> None:
        assert _strip_scheme("https://example.com") == "example.com"

    def test_strips_http(self) -> None:
        assert _strip_scheme("http://example.com") == "example.com"

    def test_bare_hostname_unchanged(self) -> None:
        assert _strip_scheme("example.com") == "example.com"

    def test_wildcard_pattern_unchanged(self) -> None:
        assert _strip_scheme("*.example.com") == "*.example.com"

    def test_strips_https_wildcard(self) -> None:
        assert _strip_scheme("https://*.example.com") == "*.example.com"

    def test_preserves_path(self) -> None:
        # Only the scheme prefix is stripped; path/port are left for the caller.
        assert _strip_scheme("https://example.com/path") == "example.com/path"

    def test_empty_string(self) -> None:
        assert _strip_scheme("") == ""


class TestParseOrigins:
    def test_comma_separated_string(self) -> None:
        result = Settings.parse_origins("example.com, other.com")
        assert result == ["example.com", "other.com"]

    def test_strips_schemes_from_string(self) -> None:
        result = Settings.parse_origins("https://example.com,http://other.com")
        assert result == ["example.com", "other.com"]

    def test_list_passthrough(self) -> None:
        result = Settings.parse_origins(["example.com", "other.com"])
        assert result == ["example.com", "other.com"]

    def test_strips_schemes_from_list(self) -> None:
        result = Settings.parse_origins(["https://example.com", "other.com"])
        assert result == ["example.com", "other.com"]

    def test_filters_empty_entries(self) -> None:
        result = Settings.parse_origins("example.com,,  ,other.com")
        assert result == ["example.com", "other.com"]

    def test_single_value(self) -> None:
        result = Settings.parse_origins("example.com")
        assert result == ["example.com"]

    def test_wildcard_pattern_preserved(self) -> None:
        result = Settings.parse_origins("*.example.com")
        assert result == ["*.example.com"]

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("https://a.com,*.b.com,http://c.com", ["a.com", "*.b.com", "c.com"]),
            (["https://a.com", "b.com"], ["a.com", "b.com"]),
        ],
    )
    def test_mixed_inputs(self, raw: str | list[str], expected: list[str]) -> None:
        assert Settings.parse_origins(raw) == expected
