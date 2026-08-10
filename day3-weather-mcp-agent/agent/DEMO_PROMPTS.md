# Agent Demo Prompts

Capture screenshots showing the natural-language prompt, tool call(s), tool result, and final agent answer for at least these three cases.

## Demo 1 — Current conditions

**Prompt**

> What is the weather in Chicago right now?

**Expected tool**

`get_current_weather(location="Chicago, IL")`

**What this proves**

Current-conditions capability and factual tool grounding.

## Demo 2 — Multi-day forecast

**Prompt**

> Will it rain in Austin over the next 3 days?

**Expected tool**

`get_forecast(location="Austin, TX", days=3)`

**What this proves**

Forecast capability and multi-day weather reasoning.

## Demo 3 — Recommendation / prediction

**Prompt**

> I am visiting Seattle tomorrow. Should I bring an umbrella and a jacket?

**Expected tool flow**

1. `get_forecast(location="Seattle, WA", days=2)` when the agent needs forecast context.
2. `get_travel_recommendation(location="Seattle, WA", date="tomorrow")`.

**What this proves**

The required derived judgment tool uses explicit thresholds rather than echoing raw API values.

## Optional stretch demo — Compare cities

**Prompt**

> Compare today's weather in Miami, Denver, and San Diego and tell me which looks most comfortable.

**Expected tool**

`compare_weather(locations=["Miami, FL", "Denver, CO", "San Diego, CA"])`
