# Agent Demo Prompts

The following prompts were used for final validation. Screenshots in `../evidence/` show the natural-language prompt, MCP tool call, tool result, and grounded answer.

## Demo 1 — Current conditions

**Prompt**

> What is the current weather in Chicago?

**Expected tool**

`get_current_weather(location="Chicago")`

**Evidence**

- `02_playground_current_weather.png`
- `06_agent_current_weather.png`

**What this proves**

Current-conditions capability and factual tool grounding.

## Demo 2 — Multi-day forecast

**Prompt**

> What is the forecast for Austin, Texas for the next 3 days?

**Expected tool**

`get_forecast(location="Austin, Texas", days=3)`

**Evidence**

- `03_playground_forecast.png`
- `07_agent_forecast.png`

**What this proves**

Multi-day forecast capability and correct argument selection.

## Demo 3 — Recommendation / prediction

**Prompt**

> I am visiting Seattle tomorrow. Should I bring an umbrella and a jacket?

**Expected tool**

`get_travel_recommendation(location="Seattle", date="tomorrow")`

**Evidence**

- `04_playground_recommendation.png`
- `08_agent_recommendation.png`

**What this proves**

The required derived-judgment capability applies explicit weather thresholds rather than simply echoing raw API data.

## Stretch demo — Compare cities

**Prompt**

> Compare today's weather in Miami, Denver, and San Diego and tell me which looks most comfortable.

**Expected tool**

`compare_weather(locations=["Miami", "Denver", "San Diego"])`

**Evidence**

- `05_playground_compare_weather.png`
- `09_agent_compare_weather.png`

**What this proves**

The MCP server exposes an additional derived comparison tool beyond the three minimum required capabilities.
