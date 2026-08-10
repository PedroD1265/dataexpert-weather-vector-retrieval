# Databricks Agent Bricks Configuration

## Agent name

`weather-intelligence-agent`

## Agent type

Custom/tool-calling agent (use the Agent Bricks option available in the workspace that supports custom MCP tools).

## MCP server

Custom MCP server hosted as a Databricks App.

App name:

`mcp-weather-intelligence`

MCP endpoint:

`https://mcp-weather-intelligence-7405607999696356.16.azure.databricksapps.com/mcp`

The MCP server is verified as **Active** in Unity AI Gateway.

## Enabled tools

- `get_current_weather`
- `get_forecast`
- `get_travel_recommendation`
- `compare_weather`

## System prompt

Use the full prompt in `SYSTEM_PROMPT.md`.

## Authentication

The Open-Meteo weather API requires no API key, so no third-party secret is stored or committed. Access to the custom MCP server is governed by Databricks App/agent permissions.

## Required final validation

Before submission, verify that the agent can use the MCP server and capture at least three screenshots showing:

1. Natural-language user prompt.
2. MCP tool call.
3. Tool result.
4. Final grounded agent answer.
