# Databricks Agent Configuration

## Final Agent App

App name:

`agent-mcp-weather-intelligence`

App URL:

`https://agent-mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com`

Status:

**Running / Active**

Final model:

`Llama 4 Maverick`

MLflow experiment:

`55555632457603`

The agent was exported from a tool-enabled Databricks AI Playground configuration into Databricks Apps and then validated again in the deployed Agent App.

## MCP server

Custom MCP server hosted as a Databricks App.

App name:

`mcp-weather-intelligence`

App URL:

`https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com`

Canonical MCP endpoint:

`https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com/mcp`

The MCP server is verified as **Running / Active** and is attached to the final Agent App as an app resource.

## Enabled tools

- `get_current_weather`
- `get_forecast`
- `get_travel_recommendation`
- `compare_weather` (stretch)

## System prompt

The full system instructions are stored in `SYSTEM_PROMPT.md`.

The prompt explicitly:

- routes current questions to `get_current_weather`;
- routes future questions to `get_forecast`;
- routes travel/packing questions to `get_travel_recommendation`;
- routes multi-city comparisons to `compare_weather`;
- prohibits invented weather values;
- instructs the agent to explain failures rather than guess;
- labels recommendation/comfort logic as project heuristics rather than official safety guidance.

## Authentication

Open-Meteo requires no API key. No third-party secret is stored or committed.

On-Behalf-Of (OBO) authentication was not required for this homework configuration; the deployed agent uses the Databricks App/service-principal resource permissions created for the MCP connection.

## Final validation

Verified in the deployed Agent App:

1. `What is the current weather in Chicago?` -> `get_current_weather`
2. `What is the forecast for Austin, Texas for the next 3 days?` -> `get_forecast`
3. `I am visiting Seattle tomorrow. Should I bring an umbrella and a jacket?` -> `get_travel_recommendation`
4. `Compare today's weather in Miami, Denver, and San Diego and tell me which looks most comfortable.` -> `compare_weather`

Screenshots are included in `../evidence/`.
