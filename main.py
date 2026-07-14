"""
Python MCP Weather Server entrypoint. Exposes check_weather as an MCP tool over stdio.
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from config import (
    ALLOW_DEMO_FALLBACK,
    DEMO_MODE,
    WEATHER_BASE_URL,
    WEATHER_TIMEOUT_SECONDS,
    configure_logging,
)
from tools.weather import fetch_weather_agent_ready

configure_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP("Python MCP Weather Server", version="0.2.0")


@mcp.tool()
async def check_weather(location: str) -> dict[str, Any]:
    """
    Return current weather for a city or place.

    Validates location, fetches from wttr.in, observes response quality, and retries
    once with an alternate spelling. On network failure, returns a demo stub with
    demo=True when fallback is enabled.
    """
    try:
        return fetch_weather_agent_ready(
            location,
            timeout_seconds=WEATHER_TIMEOUT_SECONDS,
            base_url=WEATHER_BASE_URL,
            demo_mode=DEMO_MODE,
            allow_demo_fallback=ALLOW_DEMO_FALLBACK,
        )
    except ValueError as e:
        logger.warning("Invalid location %r: %s", location, e)
        return {
            "location": location,
            "summary": "",
            "raw": "",
            "success": False,
            "demo": False,
            "error": str(e),
            "observation": {"ok": False, "reason": "validation_error", "score": 0.0},
            "attempts": 0,
            "retried_location": None,
        }


if __name__ == "__main__":
    logger.info(
        "Starting Python MCP Weather Server (stdio) demo_mode=%s allow_demo_fallback=%s",
        DEMO_MODE,
        ALLOW_DEMO_FALLBACK,
    )
    mcp.run(transport="stdio")
