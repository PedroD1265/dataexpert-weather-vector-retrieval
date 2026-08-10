# Day 3 Submission Evidence

This folder contains the final evidence for the Weather Prediction MCP Server + Agent homework.

## MCP server

1. `01_mcp_server_active.png`
   - Shows the deployed `mcp-weather-intelligence` service/health response and the exposed weather tools.

## AI Playground validation

2. `02_playground_current_weather.png`
   - Natural-language Chicago current-weather question.
   - `get_current_weather` tool call.
   - Tool output and grounded answer.

3. `03_playground_forecast.png`
   - Austin 3-day forecast question.
   - `get_forecast` tool call with `days=3`.
   - Forecast output and final answer.

4. `04_playground_recommendation.png`
   - Seattle umbrella/jacket question.
   - `get_travel_recommendation` tool call.
   - Derived recommendation, thresholds, and final answer.

5. `05_playground_compare_weather.png`
   - Stretch comparison across Miami, Denver, and San Diego.
   - `compare_weather` tool call.
   - Ranked result using the project comfort score.

## Final deployed Agent App validation

6. `06_agent_current_weather.png`
   - Deployed `agent-mcp-weather-intelligence` calling `get_current_weather` successfully.

7. `07_agent_forecast.png`
   - Deployed Agent App calling `get_forecast` successfully for Austin over 3 days.

8. `08_agent_recommendation.png`
   - Deployed Agent App calling `get_travel_recommendation` successfully for Seattle tomorrow.

9. `09_agent_compare_weather.png`
   - Deployed Agent App calling the stretch `compare_weather` tool successfully.

## Coverage

The evidence set proves:

- the custom MCP server is deployed;
- the required MCP tools are callable;
- the separate weather adapter returns real Open-Meteo data;
- the recommendation tool performs derived threshold-based logic;
- AI Playground can discover and call the MCP server;
- the final Databricks Agent App can call the MCP server end-to-end;
- at least three different natural-language questions are demonstrated, as required;
- the optional multi-city comparison stretch tool also works.

No screenshot is intended to expose passwords, API keys, tokens, cookies, or other secret values.
