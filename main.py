"""
Python MCP Weather Server entrypoint. Exposes check_weather as an MCP tool over stdio.
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from config import (
    WEATHER_BASE_URL,
    WEATHER_TIMEOUT_SECONDS,
    configure_logging,
)
from tools.weather import get_weather

configure_logging()
logger = logging.getLogger(__name__)

mcp = FastMCP("Python MCP Weather Server", version="0.1.0")


@mcp.tool()
async def check_weather(location: str) -> dict[str, Any]:
    """
    Return current weather for a city or place. Uses wttr.in; no API key required.
    """
    try:
        return get_weather(
            location,
            timeout_seconds=WEATHER_TIMEOUT_SECONDS,
            base_url=WEATHER_BASE_URL,
        )
    except ValueError as e:
        logger.warning("Invalid location %r: %s", location, e)
        return {
            "location": location,
            "summary": "",
            "raw": "",
            "success": False,
            "error": str(e),
        }


if __name__ == "__main__":
    logger.info("Starting Python MCP Weather Server (stdio)")
    mcp.run(transport="stdio")
