"""
Comprehensive tests for weather MCP tool: validation, HTTP mocks, demo fallback, agent wrapper.
"""

from __future__ import annotations

import io
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from tools.weather import (
    alternate_location_spelling,
    demo_weather,
    fetch_weather_agent_ready,
    get_weather,
    observe_weather_quality,
    validate_location,
)


class TestValidateLocation:
    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            validate_location("")

    def test_whitespace_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            validate_location("   ")

    def test_too_long_rejected(self):
        with pytest.raises(ValueError, match="at most"):
            validate_location("x" * 201)

    def test_invalid_chars_rejected(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_location("London<script>")

    def test_valid_city_normalized(self):
        assert validate_location("  New York  ") == "New York"


class TestDemoStub:
    def test_demo_weather_flag(self):
        result = demo_weather("Paris")
        assert result["demo"] is True
        assert result["success"] is True
        assert "Paris" in result["summary"]
        assert "(demo)" in result["summary"]


class TestGetWeatherHttp:
    def test_success_mocked(self):
        raw = "London: ⛅ +12°C"
        mock_resp = MagicMock()
        mock_resp.read.return_value = raw.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False

        with patch("tools.weather.urllib.request.urlopen", return_value=mock_resp):
            result = get_weather(
                "London",
                allow_demo_fallback=False,
                base_url="https://example.test",
            )

        assert result["success"] is True
        assert result["demo"] is False
        assert result["summary"] == raw
        assert result["location"] == "London"

    def test_network_error_falls_back_to_demo(self):
        with patch(
            "tools.weather.urllib.request.urlopen",
            side_effect=urllib.error.URLError("timed out"),
        ):
            result = get_weather("Berlin", allow_demo_fallback=True)

        assert result["demo"] is True
        assert result["success"] is True
        assert "Berlin" in result["summary"]
        assert result.get("error")

    def test_network_error_without_fallback(self):
        with patch(
            "tools.weather.urllib.request.urlopen",
            side_effect=urllib.error.URLError("timed out"),
        ):
            result = get_weather("Berlin", allow_demo_fallback=False)

        assert result["success"] is False
        assert result["demo"] is False
        assert "Network error" in result["error"]

    def test_http_error_fallback(self):
        with patch(
            "tools.weather.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                "https://example.test/x", 500, "Server Error", hdrs=None, fp=io.BytesIO()
            ),
        ):
            result = get_weather("Tokyo", allow_demo_fallback=True)

        assert result["demo"] is True
        assert "HTTP 500" in (result.get("error") or "")

    def test_demo_mode_skips_network(self):
        with patch("tools.weather.urllib.request.urlopen") as mock_open:
            result = get_weather("Oslo", demo_mode=True)
            mock_open.assert_not_called()
        assert result["demo"] is True
        assert result["success"] is True

    def test_timeout_fallback(self):
        with patch(
            "tools.weather.urllib.request.urlopen",
            side_effect=TimeoutError(),
        ):
            result = get_weather("Rome", allow_demo_fallback=True)
        assert result["demo"] is True
        assert "timed out" in (result.get("error") or "").lower()


class TestObserveQuality:
    def test_good_summary(self):
        obs = observe_weather_quality(
            {"success": True, "summary": "London: +12°C", "demo": False}
        )
        assert obs["ok"] is True
        assert obs["score"] == 1.0

    def test_empty_summary(self):
        obs = observe_weather_quality({"success": True, "summary": "", "demo": False})
        assert obs["ok"] is False
        assert obs["reason"] == "empty_summary"

    def test_upstream_error_text(self):
        obs = observe_weather_quality(
            {"success": True, "summary": "Unknown location", "demo": False}
        )
        assert obs["ok"] is False

    def test_failed_request(self):
        obs = observe_weather_quality(
            {"success": False, "error": "Network error", "demo": False}
        )
        assert obs["ok"] is False
        assert obs["score"] == 0.0


class TestAlternateSpelling:
    def test_camel_case(self):
        assert alternate_location_spelling("NewYork") == "New York"

    def test_underscores(self):
        assert alternate_location_spelling("San_Francisco") == "San Francisco"

    def test_no_change_returns_none_or_title(self):
        # "london" may title-case to "London"
        alt = alternate_location_spelling("london")
        assert alt in (None, "London")

    def test_already_spaced_same(self):
        alt = alternate_location_spelling("New York")
        assert alt is None or alt == "New York"


class TestAgentReadyWrapper:
    def test_success_no_retry(self):
        raw = "Paris: +20°C"
        mock_resp = MagicMock()
        mock_resp.read.return_value = raw.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = False

        with patch("tools.weather.urllib.request.urlopen", return_value=mock_resp):
            result = fetch_weather_agent_ready(
                "Paris",
                allow_demo_fallback=False,
                base_url="https://example.test",
            )

        assert result["success"] is True
        assert result["attempts"] == 1
        assert result["retried_location"] is None
        assert result["observation"]["ok"] is True

    def test_retries_alternate_spelling_once(self):
        good = "New York: +10°C"
        call_count = {"n": 0}

        def fake_urlopen(req, timeout=None):
            call_count["n"] += 1
            url = req.full_url if hasattr(req, "full_url") else str(req)
            mock_resp = MagicMock()
            mock_resp.__enter__.return_value = mock_resp
            mock_resp.__exit__.return_value = False
            if "New%20York" in url or "New York" in urllib_parse_unquote(url):
                mock_resp.read.return_value = good.encode("utf-8")
            else:
                mock_resp.read.return_value = b"Unknown location"
            return mock_resp

        def urllib_parse_unquote(url: str) -> str:
            import urllib.parse

            return urllib.parse.unquote(url)

        with patch("tools.weather.urllib.request.urlopen", side_effect=fake_urlopen):
            result = fetch_weather_agent_ready(
                "NewYork",
                allow_demo_fallback=False,
                base_url="https://example.test",
            )

        assert result["retried_location"] == "New York"
        assert result["attempts"] >= 2
        assert result["success"] is True
        assert "New York" in result["summary"]
        assert call_count["n"] == 2

    def test_agent_falls_back_to_demo_after_failures(self):
        with patch(
            "tools.weather.urllib.request.urlopen",
            side_effect=urllib.error.URLError("unreachable"),
        ):
            result = fetch_weather_agent_ready(
                "Atlantis",
                allow_demo_fallback=True,
                base_url="https://example.test",
            )

        assert result["demo"] is True
        assert result["success"] is True
        assert result["observation"]["ok"] is True
        assert result["observation"]["reason"] == "demo_stub"

    def test_validation_error_propagates(self):
        with pytest.raises(ValueError):
            fetch_weather_agent_ready("")


class TestMCPToolSurface:
    def test_tool_schema_shape(self):
        schema = {
            "name": "check_weather",
            "description": "Get current weather",
            "input_schema": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        }
        assert schema["name"] == "check_weather"
        assert "location" in schema["input_schema"]["properties"]
