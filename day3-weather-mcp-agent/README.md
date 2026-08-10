# Weather Prediction MCP Server + Agent

DataExpert.io **Rise of the AI Data Engineer — Day 3 Homework**.

This project implements a custom FastMCP weather server backed by the free Open-Meteo API and a Databricks Agent Bricks agent that uses the MCP tools to answer grounded weather questions and make simple recommendations.

## Deployed MCP App

- Databricks App: `mcp-weather-intelligence`
- App URL: `https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com`
- MCP endpoint: `https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com/mcp`
- Verified status: **Active** in Databricks Apps and Unity AI Gateway.

## Architecture

```text
User
  |
  v
Databricks Agent Bricks
  |
  | MCP tool calls
  v
Databricks App: mcp-weather-intelligence
  |
  v
FastMCP (streamable HTTP /mcp)
  |
  +--> get_current_weather
  +--> get_forecast
  +--> get_travel_recommendation
  +--> compare_weather
             |
             v
       weather_adapter.py
             |
             v
        Open-Meteo API
```

The MCP tool functions stay thin. All HTTP requests, location resolution, normalization, and recommendation logic live in `mcp_server/weather_adapter.py`.

## Weather API

**Open-Meteo** was selected because it is free for educational/non-commercial use and does not require an API key or credit card to start. This removes secret-management overhead while still providing geocoding, current conditions, and multi-day forecasts.

No API key, password, or secret is hard-coded or committed to this repository.

## MCP tools

### `get_current_weather(location)`

Returns normalized current conditions including temperature, feels-like temperature, humidity, precipitation, wind, gusts, and a WMO weather description.

### `get_forecast(location, days=5)`

Returns a 1-7 day forecast with high/low temperatures, precipitation probability/amount, conditions, and wind/gust values.

### `get_travel_recommendation(location, date="tomorrow")`

Required derived-judgment tool. It applies explicit deterministic thresholds:

- umbrella when precipitation probability is >= 40% or precipitation >= 0.05 in;
- jacket when the forecast low is <= 55°F;
- heat precautions when the forecast high is >= 85°F;
- wind caution when gusts are >= 30 mph;
- additional caution for thunderstorm/wintry WMO codes.

The tool returns both the recommendation and the exact forecast values/reasons that triggered it.

### `compare_weather(locations)`

Stretch tool that compares 2-5 cities and ranks them using a simple comfort score based on temperature, precipitation probability, and wind gusts.

## Project structure

```text
day3-weather-mcp-agent/
├── README.md
├── SUBMISSION.md
├── SUBMISSION_CHECKLIST.md
│
├── mcp_server/
│   ├── weather_mcp_server.py
│   ├── weather_adapter.py
│   ├── app.yaml
│   └── requirements.txt
│
├── agent/
│   ├── SYSTEM_PROMPT.md
│   ├── TOOL_LIST.md
│   ├── AGENT_CONFIG.md
│   └── DEMO_PROMPTS.md
│
└── evidence/
    └── README.md
```

## Deploy the MCP server

Create a Databricks App named:

`mcp-weather-intelligence`

Deploy it from the `day3-weather-mcp-agent/mcp_server/` folder. The app runs:

```text
python weather_mcp_server.py
```

FastMCP uses streamable HTTP transport and exposes the MCP endpoint at:

```text
https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com/mcp
```

## Register/connect the MCP server to the agent

The deployed custom MCP App is visible as **Active** in Unity AI Gateway. Use it from AI Playground / Agent Bricks and confirm tool calls for:

- `get_current_weather`
- `get_forecast`
- `get_travel_recommendation`
- `compare_weather`

Use `agent/SYSTEM_PROMPT.md` as the agent's system instructions.

## Required demonstrations

Capture at least three natural-language agent interactions showing both the tool call and final answer. Recommended cases are documented in `agent/DEMO_PROMPTS.md`:

1. Current weather in Chicago.
2. Three-day rain forecast in Austin.
3. Umbrella/jacket recommendation for Seattle tomorrow.

Optional stretch: compare weather across multiple cities.

## Error handling

- Blank/unresolvable locations return a clean tool error rather than a Python stack trace.
- HTTP failures and invalid JSON are converted to a structured error response.
- Invalid dates return a clear message.
- Forecast-day values are clamped to 1-7.
- The agent prompt explicitly instructs the model not to invent weather values when a tool call fails.

## Known limitations / next improvements

- The project intentionally uses Open-Meteo only; official severe-weather alerts are not included.
- The recommendation thresholds are simple educational heuristics, not official safety guidance.
- A future version could add NWS severe-weather alerts as a second source and log agent/tool interactions to Lakebase for observability.

## Security

No third-party API credentials are required. No secrets, tokens, passwords, or API keys are committed to the repository.
