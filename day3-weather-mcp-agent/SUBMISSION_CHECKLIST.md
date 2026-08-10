# Day 3 Weather MCP Homework Checklist

## MCP server

- FastMCP server: **IMPLEMENTED**
- HTTP/streamable transport: **IMPLEMENTED**
- Databricks App `app.yaml`: **IMPLEMENTED**
- `requirements.txt`: **IMPLEMENTED**
- Separate adapter module: **IMPLEMENTED**
- No raw `requests` calls inside `@mcp.tool` functions: **VERIFIED**

## Required tools

- Current conditions: `get_current_weather`: **IMPLEMENTED**
- Multi-day forecast: `get_forecast`: **IMPLEMENTED**
- Derived recommendation: `get_travel_recommendation`: **IMPLEMENTED**
- Stretch comparison tool: `compare_weather`: **IMPLEMENTED**

## Quality

- Tool docstrings include Args/Returns: **IMPLEMENTED**
- Clean bad-location/API error handling: **IMPLEMENTED**
- Recommendation uses explicit thresholds: **IMPLEMENTED**
- No hard-coded secrets/API keys: **VERIFIED**
- Open-Meteo requires no credentials: **VERIFIED**

## Agent Bricks

- System prompt: **IMPLEMENTED**
- Tool list: **IMPLEMENTED**
- Agent configuration notes: **IMPLEMENTED**
- Anti-hallucination guardrails: **IMPLEMENTED**
- MCP server deployed as Databricks App: **PENDING MANUAL DEPLOYMENT**
- MCP connected to Agent Bricks: **PENDING MANUAL CONFIGURATION**
- Agent deployed/tested: **PENDING MANUAL CONFIGURATION**

## Demonstration evidence

- Demo 1 — current weather: **PENDING SCREENSHOT**
- Demo 2 — multi-day forecast: **PENDING SCREENSHOT**
- Demo 3 — travel recommendation: **PENDING SCREENSHOT**
- MCP tool discovery screenshot: **PENDING SCREENSHOT**
- Databricks App deployment screenshot: **PENDING SCREENSHOT**

## Submission

- README: **INCLUDED**
- GitHub repository: **INCLUDED**
- GitHub branch: **INCLUDED**
- MCP App URL: **TO ADD AFTER DEPLOYMENT**
- Final source ZIP: **TO EXPORT AFTER FINAL TEST**
- Evidence screenshots: **TO CAPTURE AFTER FINAL TEST**
