"""
Weather lookup via wttr.in: validation, timeouts, demo fallback, and agent-ready fetch.
"""

from __future__ import annotations

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

# Quality: wttr format=3 looks like "City: +12°C" or "City: ⛅ +12°C"
_QUALITY_OK = re.compile(r".+:\s*.*\d")
_CAMEL_SPLIT = re.compile(r"(?<=[a-z])(?=[A-Z])")


def validate_location(location: str) -> str:
    """Validate and normalize location input. Returns stripped location."""
    if not location or not (s := location.strip()):
        raise ValueError("Location cannot be empty")
    if len(s) > MAX_LOCATION_LENGTH:
        raise ValueError(f"Location must be at most {MAX_LOCATION_LENGTH} characters")
    if not ALLOWED_LOCATION_PATTERN.match(s):
        raise ValueError(
            "Location contains invalid characters; use letters, numbers, spaces, "
            "hyphens, commas, periods, apostrophes"
        )
    return s


def _validate_location(location: str) -> None:
    """Validate location (legacy name used by tests / callers)."""
    validate_location(location)


def demo_weather(location: str) -> dict[str, Any]:
    """Deterministic stub weather for offline / network-failure demo paths."""
    loc = location.strip() or "Unknown"
    summary = f"{loc}: +18°C (demo)"
    return {
        "location": loc,
        "summary": summary,
        "raw": summary,
        "success": True,
        "demo": True,
        "error": None,
    }


def observe_weather_quality(result: dict[str, Any]) -> dict[str, Any]:
    """
    Observe fetch quality for agent revise loops.

    Returns a small observation dict: ok, reason, score (0.0–1.0).
    """
    if result.get("demo"):
        return {"ok": True, "reason": "demo_stub", "score": 0.5}

    if not result.get("success"):
        return {
            "ok": False,
            "reason": result.get("error") or "request_failed",
            "score": 0.0,
        }

    summary = (result.get("summary") or result.get("raw") or "").strip()
    if not summary:
        return {"ok": False, "reason": "empty_summary", "score": 0.0}

    lower = summary.lower()
    if any(bad in lower for bad in ("unknown location", "not found", "error", "sorry")):
        return {"ok": False, "reason": "upstream_error_text", "score": 0.1}

    if _QUALITY_OK.search(summary):
        return {"ok": True, "reason": "structured_summary", "score": 1.0}

    if len(summary) >= 3:
        return {"ok": True, "reason": "nonempty_summary", "score": 0.7}

    return {"ok": False, "reason": "low_quality_summary", "score": 0.2}


def alternate_location_spelling(location: str) -> str | None:
    """
    Produce one alternate spelling for a retry (underscores→spaces, camelCase split).

    Returns None when no distinct alternate exists.
    """
    original = location.strip()
    if not original:
        return None

    candidate = original.replace("_", " ").replace("-", " ")
    candidate = _CAMEL_SPLIT.sub(" ", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip()

    if candidate.lower() == original.lower() or not candidate:
        # Title-case single token as a last mild alternate
        titled = original.title()
        if titled != original:
            return titled
        return None

    return candidate


def get_weather(
    location: str,
    *,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    base_url: str = "https://wttr.in",
    demo_mode: bool = False,
    allow_demo_fallback: bool = True,
) -> dict[str, Any]:
    """
    Fetch weather for a given location from wttr.in.

    On network / HTTP failure, optionally returns a demo stub with ``demo=True``.

    Returns:
        Dict with keys: location, summary, raw, success, demo; and optionally error.
    """
    loc = validate_location(location)

    if demo_mode:
        logger.info("DEMO_MODE: returning stub weather for location=%r", loc)
        return demo_weather(loc)

    encoded = urllib.parse.quote(loc, safe="")
    url = f"{base_url.rstrip('/')}/{encoded}?format=3"

    result: dict[str, Any] = {
        "location": loc,
        "summary": "",
        "raw": "",
        "success": False,
        "demo": False,
    }

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "python-mcp-weather-server/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace").strip()
            result["raw"] = raw
            result["summary"] = raw
            result["success"] = True
            logger.info("Weather fetched for location=%r", loc)
            return result
    except urllib.error.HTTPError as e:
        result["error"] = f"HTTP {e.code}: {e.reason}"
        logger.warning("Weather HTTP error for %r: %s", loc, e)
    except urllib.error.URLError as e:
        result["error"] = f"Network error: {e.reason}"
        logger.warning("Weather URL error for %r: %s", loc, e)
    except TimeoutError:
        result["error"] = "Request timed out"
        logger.warning("Weather timeout for %r", loc)
    except OSError as e:
        result["error"] = str(e)
        logger.exception("Weather request failed for %r", loc)

    if allow_demo_fallback:
        stub = demo_weather(loc)
        stub["error"] = result.get("error")
        logger.warning(
            "Falling back to DEMO stub for %r after failure: %s",
            loc,
            result.get("error"),
        )
        return stub

    return result


def fetch_weather_agent_ready(
    location: str,
    *,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    base_url: str = "https://wttr.in",
    demo_mode: bool = False,
    allow_demo_fallback: bool = True,
) -> dict[str, Any]:
    """
    Agent-ready wrapper: validate → fetch → observe quality → retry alternate spelling once.

    Adds ``observation``, ``attempts``, and ``retried_location`` metadata for agents.
    """
    loc = validate_location(location)
    attempts: list[dict[str, Any]] = []
    # Skip per-call demo so we can observe and retry spelling before falling back
    skip_demo = not demo_mode

    first = get_weather(
        loc,
        timeout_seconds=timeout_seconds,
        base_url=base_url,
        demo_mode=demo_mode,
        allow_demo_fallback=not skip_demo,
    )
    obs = observe_weather_quality(first)
    attempts.append({"location": loc, "result": first, "observation": obs})

    final = first
    retried_location: str | None = None

    if not obs["ok"] and not first.get("demo"):
        alt = alternate_location_spelling(loc)
        if alt and alt.lower() != loc.lower():
            try:
                validate_location(alt)
            except ValueError:
                alt = None
            if alt:
                retried_location = alt
                second = get_weather(
                    alt,
                    timeout_seconds=timeout_seconds,
                    base_url=base_url,
                    demo_mode=demo_mode,
                    allow_demo_fallback=not skip_demo,
                )
                obs2 = observe_weather_quality(second)
                attempts.append(
                    {"location": alt, "result": second, "observation": obs2}
                )
                if obs2["ok"] or obs2["score"] > obs["score"]:
                    final = second
                    obs = obs2

    if not obs["ok"] and not final.get("demo") and allow_demo_fallback:
        stub = demo_weather(loc)
        stub["error"] = final.get("error") or obs.get("reason")
        final = stub
        obs = observe_weather_quality(final)
        attempts.append({"location": loc, "result": final, "observation": obs})

    out = dict(final)
    out["observation"] = obs
    out["attempts"] = len(attempts)
    out["retried_location"] = retried_location
    return out
