# MCP Tool List

The Databricks Agent Bricks agent should be connected to the custom MCP server and allowed to use these tools:

## 1. `get_current_weather(location)`

Purpose: current observed conditions.

Returns temperature, feels-like temperature, humidity, precipitation, wind, gusts, weather code/description, observation time, resolved location, and provider metadata.

## 2. `get_forecast(location, days=5)`

Purpose: multi-day forecast.

Returns daily high/low temperature, precipitation probability, precipitation amount, conditions, max wind, and max gusts for 1-7 days.

## 3. `get_travel_recommendation(location, date="tomorrow")`

Purpose: derived recommendation rather than raw API passthrough.

Deterministic thresholds:

- Umbrella: precipitation probability >= 40% OR precipitation >= 0.05 in.
- Jacket: forecast low <= 55°F.
- Heat precautions: forecast high >= 85°F.
- Wind caution: gusts >= 30 mph.
- Thunderstorm/wintry codes trigger additional outdoor caution.

Returns the underlying forecast, recommendation flags, packing suggestions, reasons, and the thresholds applied.

## 4. `compare_weather(locations)` — stretch tool

Purpose: compare today's weather across 2-5 cities.

Returns a ranked comparison with a simple comfort score favoring temperatures near 72°F, lower precipitation probability, and lower wind gusts. The score is explicitly a project heuristic, not a safety rating.
