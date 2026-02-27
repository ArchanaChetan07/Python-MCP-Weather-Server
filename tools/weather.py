"""
Weather lookup via wttr.in: validation, timeouts, and a consistent response shape.
"""

import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

# Limits for production safety
MAX_LOCATION_LENGTH = 200
REQUEST_TIMEOUT_SECONDS = 10
ALLOWED_LOCATION_PATTERN = re.compile(r"^[\w\s\-.,']+$", re.UNICODE)


def _validate_location(location: str) -> None:
    """Validate and sanitize location input."""
    if not location or not (s := location.strip()):
        raise ValueError("Location cannot be empty")
    if len(s) > MAX_LOCATION_LENGTH:
        raise ValueError(f"Location must be at most {MAX_LOCATION_LENGTH} characters")
    if not ALLOWED_LOCATION_PATTERN.match(s):
        raise ValueError(
            "Location contains invalid characters; use letters, numbers, spaces, hyphens, commas, periods, apostrophes"
        )


def get_weather(
    location: str,
    *,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    base_url: str = "https://wttr.in",
) -> dict[str, Any]:
    """
    Fetch weather for a given location from wttr.in.

    Args:
        location: City or place name (e.g. "New York", "London").
        timeout_seconds: Request timeout in seconds.
        base_url: wttr.in base URL (for tests or alternate instances).

    Returns:
        Dict with keys: location, summary, raw, success; and optionally error.
    """
    _validate_location(location)
    encoded = urllib.parse.quote(location.strip(), safe="")
    url = f"{base_url.rstrip('/')}/{encoded}?format=3"

    result: dict[str, Any] = {
        "location": location.strip(),
        "summary": "",
        "raw": "",
        "success": False,
    }

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "python-mcp-weather-server/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace").strip()
            result["raw"] = raw
            result["summary"] = raw
            result["success"] = True
            logger.info("Weather fetched for location=%r", location.strip())
            return result
    except urllib.error.HTTPError as e:
        result["error"] = f"HTTP {e.code}: {e.reason}"
        logger.warning("Weather HTTP error for %r: %s", location, e)
        return result
    except urllib.error.URLError as e:
        result["error"] = f"Network error: {e.reason}"
        logger.warning("Weather URL error for %r: %s", location, e)
        return result
    except TimeoutError:
        result["error"] = "Request timed out"
        logger.warning("Weather timeout for %r", location)
        return result
    except OSError as e:
        result["error"] = str(e)
        logger.exception("Weather request failed for %r", location)
        return result
