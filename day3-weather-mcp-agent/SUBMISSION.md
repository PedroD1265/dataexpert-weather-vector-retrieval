# Day 3 Homework Submission — Weather MCP Server + Agent

## Source repository

Repository:

`https://github.com/PedroD1265/dataexpert-weather-vector-retrieval`

Branch:

`day3-weather-mcp-agent`

Submission project folder:

`day3-weather-mcp-agent/`

## Databricks MCP App

App name:

`mcp-weather-intelligence`

App URL:

`https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com`

Canonical MCP endpoint:

`https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com/mcp`

Status: **Running / Active**.

## Databricks Agent App

App name:

`agent-mcp-weather-intelligence`

App URL:

`https://agent-mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com`

Final model:

`Llama 4 Maverick`

MLflow experiment:

`55555632457603`

MCP resource:

`mcp-weather-intelligence`

System prompt:

`agent/SYSTEM_PROMPT.md`

Tool list:

`agent/TOOL_LIST.md`

Enabled tools:

- `get_current_weather`
- `get_forecast`
- `get_travel_recommendation`
- `compare_weather` (stretch)

Status: **Running / Active and functionally verified**.

## Demonstration evidence

The `evidence/` folder contains nine screenshots:

1. `01_mcp_server_active.png` — MCP server health/status and exposed tool list.
2. `02_playground_current_weather.png` — current-weather tool call in AI Playground.
3. `03_playground_forecast.png` — multi-day forecast tool call in AI Playground.
4. `04_playground_recommendation.png` — derived travel recommendation in AI Playground.
5. `05_playground_compare_weather.png` — stretch city comparison in AI Playground.
6. `06_agent_current_weather.png` — deployed Agent App calling `get_current_weather`.
7. `07_agent_forecast.png` — deployed Agent App calling `get_forecast`.
8. `08_agent_recommendation.png` — deployed Agent App calling `get_travel_recommendation`.
9. `09_agent_compare_weather.png` — deployed Agent App calling `compare_weather`.

The three required natural-language demonstrations are therefore verified in both Playground and the final deployed Agent App.

## Architecture summary

```text
User
  -> Databricks Agent App
  -> custom MCP tool call
  -> mcp-weather-intelligence Databricks App
  -> FastMCP
  -> weather_adapter.py
  -> Open-Meteo API
```

## Security

Open-Meteo requires no API key. No passwords, API keys, tokens, cookies, or secret values are included in source control or the submission.

## ZIP to submit

Create the ZIP from **only** the `day3-weather-mcp-agent/` folder after pulling the final branch changes.

Recommended filename:

`day3-weather-mcp-agent.zip`
