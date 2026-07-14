"""
Configuration from environment variables. Used by the MCP server at startup.
"""

import logging
import os

_DEFAULT_BASE_URL = "https://wttr.in"
_DEFAULT_TIMEOUT = 10
_MAX_TIMEOUT = 60

WEATHER_BASE_URL = (os.environ.get("WEATHER_BASE_URL") or _DEFAULT_BASE_URL).strip().rstrip("/")
if not WEATHER_BASE_URL.startswith(("http://", "https://")):
    WEATHER_BASE_URL = "https://" + WEATHER_BASE_URL

_raw_timeout = os.environ.get("WEATHER_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT))
try:
    WEATHER_TIMEOUT_SECONDS = max(1, min(int(_raw_timeout), _MAX_TIMEOUT))
except ValueError:
    WEATHER_TIMEOUT_SECONDS = _DEFAULT_TIMEOUT

# Offline / resilient demo: stub weather when DEMO_MODE=1 or when live fetch fails
DEMO_MODE = os.environ.get("DEMO_MODE", "").strip().lower() in {"1", "true", "yes"}
_ALLOW_DEMO_FALLBACK_RAW = os.environ.get("ALLOW_DEMO_FALLBACK", "1").strip().lower()
ALLOW_DEMO_FALLBACK = _ALLOW_DEMO_FALLBACK_RAW in {"1", "true", "yes"}

LOG_LEVEL = (os.environ.get("LOG_LEVEL") or "INFO").strip().upper()
if LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR"):
    LOG_LEVEL = "INFO"


def configure_logging() -> None:
    """Configure root logger for the MCP process."""
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
