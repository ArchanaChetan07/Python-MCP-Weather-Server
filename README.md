# Python MCP Weather Server

A **Python** **Model Context Protocol (MCP)** server that exposes weather lookup as a tool for AI assistants and IDEs. Calls [wttr.in](https://wttr.in) and returns structured JSON—with validation, timeouts, demo fallback, and an agent-ready observe/retry loop.

## Overview

- **Purpose:** MCP tool `check_weather(location)` returns current weather for any city or place.
- **Audience:** MCP clients (e.g. Cursor, Claude Desktop). No API key required.
- **Resilience:** Input validation, HTTP timeouts, structured errors, DEMO stub (`demo=True`) when the network fails, and one alternate-spelling retry after quality observation.

## Tech stack

- **Python 3.10+**
- **MCP SDK** ([mcp](https://github.com/modelcontextprotocol/python-sdk)) — stdio transport
- **wttr.in** — weather data (HTTP, no auth)
- **stdlib** for HTTP (urllib)

## Quick start

```bash
cd Python-MCP-Weather-Server
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python main.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEATHER_BASE_URL` | `https://wttr.in` | Upstream base URL. |
| `WEATHER_TIMEOUT_SECONDS` | `10` | Request timeout (seconds). |
| `DEMO_MODE` | off | When `1`/`true`, always return stub weather (`demo=True`). |
| `ALLOW_DEMO_FALLBACK` | `1` | On live network failure, return stub with `demo=True`. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

## Tool API

**`check_weather(location: str)`**

Flow: validate → fetch → observe quality → retry alternate spelling once → demo fallback if still failing.

| Field | Type | Description |
|-------|------|-------------|
| `location` | string | Normalized location. |
| `summary` | string | One-line weather (e.g. `London: +12°C`). |
| `raw` | string | Same as `summary`. |
| `success` | boolean | `true` if usable weather was returned (live or demo). |
| `demo` | boolean | `true` when response is a stub (offline / fallback). |
| `error` | string | Present on failure or when demo replaced a failed live call. |
| `observation` | object | Quality observe result (`ok`, `reason`, `score`). |
| `attempts` | int | Number of fetch attempts (1 or 2+ with demo). |
| `retried_location` | string\|null | Alternate spelling used on retry, if any. |

## Tests

```bash
pytest tests/ -v --tb=short
```

All HTTP calls are mocked; CI runs lint + pytest strictly (no soft-fail).

## Project structure

```
Python-MCP-Weather-Server/
├── main.py                 # MCP server and check_weather tool
├── config.py               # Env-based config and logging
├── tools/
│   ├── __init__.py
│   └── weather.py          # Validation, fetch, demo, agent wrapper
├── tests/
│   └── test_weather_server.py
├── requirements.txt
├── pyproject.toml
└── README.md
```
