# Weather Prediction MCP Server + Agent

DataExpert.io **Rise of the AI Data Engineer — Day 3 Homework**.

This project implements a custom FastMCP weather server backed by the free Open-Meteo API and a Databricks tool-calling agent that uses MCP tools to answer grounded weather questions, return multi-day forecasts, make simple travel recommendations, and compare weather across cities.

## Final deployed applications

### MCP server

- Databricks App: `mcp-weather-intelligence`
- App URL: `https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com`
- Canonical MCP endpoint: `https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com/mcp`
- Status: **Running / Active**

### Agent app

- Databricks App: `agent-mcp-weather-intelligence`
- App URL: `https://agent-mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com`
- Final model: **Llama 4 Maverick**
- MCP resource: `mcp-weather-intelligence`
- MLflow experiment: `55555632457603`
- Status: **Running / Active**

The final agent was exported from a tool-enabled Databricks AI Playground configuration and verified again in the deployed Databricks App.

## Architecture

```text
User
  |
  v
Databricks Agent App
(agent-mcp-weather-intelligence)
  |
  | MCP tool calls
  v
Databricks MCP App
(mcp-weather-intelligence)
  |
  v
FastMCP / Streamable HTTP
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

**Open-Meteo** was selected because it is free for educational/non-commercial use and does not require an API key or credit card to start. It provides the geocoding, current-condition, and forecast data required by this project without adding secret-management overhead.

No API key, password, token, or secret is hard-coded or committed to this repository.

## MCP tools

### `get_current_weather(location)`

Returns normalized current conditions including temperature, feels-like temperature, humidity, precipitation, wind, gusts, WMO weather code/description, observation time, resolved location, and provider metadata.

### `get_forecast(location, days=5)`

Returns a 1-7 day forecast with high/low temperatures, precipitation probability/amount, conditions, maximum wind, and maximum gust values.

### `get_travel_recommendation(location, date="tomorrow")`

Required derived-judgment tool. It applies deterministic thresholds rather than merely echoing raw API values:

- umbrella when precipitation probability is >= 40% or precipitation >= 0.05 in;
- jacket when the forecast low is <= 55°F;
- heat precautions when the forecast high is >= 85°F;
- wind caution when gusts are >= 30 mph;
- additional caution for thunderstorm/wintry WMO codes.

The tool returns the forecast used, recommendation flags, packing suggestions, reasons, and the exact thresholds applied.

### `compare_weather(locations)`

Stretch tool that compares 2-5 cities and ranks them using a simple comfort score based on temperature, precipitation probability, and wind gusts. The score is explicitly a project heuristic, not a safety rating.

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
    ├── 01_mcp_server_active.png
    ├── 02_playground_current_weather.png
    ├── 03_playground_forecast.png
    ├── 04_playground_recommendation.png
    ├── 05_playground_compare_weather.png
    ├── 06_agent_current_weather.png
    ├── 07_agent_forecast.png
    ├── 08_agent_recommendation.png
    ├── 09_agent_compare_weather.png
    └── README.md
```

## Deploy the MCP server

Create a Databricks App named `mcp-weather-intelligence` and deploy it from the `day3-weather-mcp-agent/mcp_server/` folder.

The included `app.yaml` starts the server with:

```text
uvicorn weather_mcp_server:app --host 0.0.0.0 --port 8000
```

FastMCP uses stateless Streamable HTTP. The canonical MCP endpoint is `/mcp`. This project also mounts a `/mcp/mcp` compatibility path because the AI Playground integration in this workspace appended `/mcp` to the registered Databricks App endpoint during testing. The official endpoint remains `/mcp`.

## Agent configuration

The agent configuration is documented in `agent/AGENT_CONFIG.md` and the full guardrail prompt is in `agent/SYSTEM_PROMPT.md`.

Enabled MCP tools:

- `get_current_weather`
- `get_forecast`
- `get_travel_recommendation`
- `compare_weather`

The final exported agent uses **Llama 4 Maverick** and the custom `mcp-weather-intelligence` Databricks App as its MCP resource.

## Verified demonstrations

Both AI Playground and the deployed Agent App were tested successfully.

Required cases:

1. `What is the current weather in Chicago?` -> `get_current_weather`
2. `What is the forecast for Austin, Texas for the next 3 days?` -> `get_forecast`
3. `I am visiting Seattle tomorrow. Should I bring an umbrella and a jacket?` -> `get_travel_recommendation`

Stretch case:

4. `Compare today's weather in Miami, Denver, and San Diego and tell me which looks most comfortable.` -> `compare_weather`

The `evidence/` folder contains the screenshots showing the natural-language prompt, MCP tool call, tool result, and final grounded answer.

## Error handling

- Blank/unresolvable locations return clean tool errors rather than Python stack traces.
- HTTP failures and invalid JSON are converted to structured error responses.
- Invalid dates return a clear message.
- Forecast-day values are clamped to 1-7.
- The agent prompt explicitly instructs the model not to invent weather values when a tool call fails.

## Known limitations / next improvements

- The project intentionally uses Open-Meteo only; official severe-weather alerts are not included.
- Recommendation thresholds are educational heuristics, not official safety guidance.
- A future version could add NWS severe-weather alerts and persist agent/tool interactions for richer observability.

## Security

Open-Meteo requires no credentials. No secrets, passwords, API keys, or tokens are included in source control or the submission.

## Final ZIP

For the homework submission, zip **this folder only**:

`day3-weather-mcp-agent/`

Do not zip the entire repository branch, because the branch also contains files from the completed Day 2 project.
