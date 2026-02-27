# Python MCP Weather Server

A **Python** **Model Context Protocol (MCP)** server that exposes weather lookup as a tool for AI assistants and IDEs. Calls [wttr.in](https://wttr.in) and returns structured JSON—production-style config, validation, and logging. Suited as a portfolio or sample project for **Python**, **MCP**, and **API** work.

## Overview

- **Purpose:** Provide a single MCP tool, `check_weather(location)`, that returns current weather for any city or place.
- **Audience:** MCP clients (e.g. Cursor, Claude Desktop). No API key required.
- **Design:** Env-based config, input validation, timeouts, structured JSON responses, and logging for production use.

## Tech stack

- **Python 3.13+**
- **MCP SDK** ([mcp](https://github.com/modelcontextprotocol/python-sdk)) — stdio transport
- **wttr.in** — weather data (HTTP, no auth)
- **stdlib only** for HTTP and config (no Flask/FastAPI)

## Quick start

```bash
cd python-mcp-weather-server
uv sync
uv run python main.py
```

Or with pip:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .
python main.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEATHER_BASE_URL` | `https://wttr.in` | Upstream base URL. |
| `WEATHER_TIMEOUT_SECONDS` | `10` | Request timeout (seconds). |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

## Usage

**Run (stdio):** `uv run python main.py` or `python main.py`.

**Cursor:** In Settings → MCP (or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "<absolute-path-to-weather-mcp>"
    }
  }
}
```

Replace `<absolute-path-to-python-mcp-weather-server>` with the project directory (e.g. `C:\\Users\\You\\Desktop\\python-mcp-weather-server` on Windows).

## Tool API

**`check_weather(location: str)`**

Returns a JSON object:

| Field | Type | Description |
|-------|------|-------------|
| `location` | string | Normalized location. |
| `summary` | string | One-line weather (e.g. `London: +12°C`). |
| `raw` | string | Same as `summary`. |
| `success` | boolean | `true` if the request succeeded. |
| `error` | string | Present only on failure. |

Success example: `{"location": "London", "summary": "London: +12°C", "raw": "London: +12°C", "success": true}`

## Technical notes

- **Validation:** Location is required, max 200 characters, and limited to safe characters (letters, digits, spaces, `-.,'`) to avoid abuse.
- **Resilience:** Timeouts and explicit handling of HTTP, network, and timeout errors; all failures return a structured `error` field.
- **Observability:** Structured logging with configurable level; no secrets in logs.

## Project structure

```
python-mcp-weather-server/
├── main.py           # MCP server and check_weather tool
├── config.py         # Env-based config and logging setup
├── tools/
│   ├── __init__.py
│   └── weather.py    # Validation, HTTP fetch, response shape
├── pyproject.toml
└── README.md
```

