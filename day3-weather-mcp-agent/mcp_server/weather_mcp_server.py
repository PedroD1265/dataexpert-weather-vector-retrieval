"""FastMCP weather server for the DataExpert Day 3 homework.

The MCP surface intentionally stays thin. All HTTP calls, parsing, and
recommendation logic live in weather_adapter.py.
"""

from __future__ import annotations

import logging
import os

from fastmcp import FastMCP

import weather_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-mcp-server")

mcp = FastMCP("weather-intelligence")


def _error(exc: Exception) -> dict:
    logger.warning("Weather tool failed: %s", exc)
    return {
        "status": "error",
        "error": str(exc),
        "instruction": "Ask the user to clarify the location/date or try again later. Do not guess weather values.",
    }


@mcp.tool
def get_current_weather(location: str) -> dict:
    """Get current weather conditions for a location.

    Args:
        location: Human-readable place name, for example "Chicago, IL" or "Austin, TX".

    Returns:
        A normalized dict with resolved location, observation time, temperature,
        feels-like temperature, humidity, precipitation, wind, gusts, conditions,
        and provider metadata. On failure, returns a clean error dict.
    """
    try:
        return weather_adapter.get_current_conditions(location)
    except weather_adapter.WeatherAdapterError as exc:
        return _error(exc)


@mcp.tool
def get_forecast(location: str, days: int = 5) -> dict:
    """Get a multi-day weather forecast for a location.

    Args:
        location: Human-readable place name, for example "Seattle, WA".
        days: Number of forecast days to return. Values are clamped to 1-7.

    Returns:
        A dict containing daily high/low temperatures, precipitation chance,
        precipitation amount, weather conditions, max wind, and max gusts.
    """
    try:
        return weather_adapter.get_daily_forecast(location, days)
    except weather_adapter.WeatherAdapterError as exc:
        return _error(exc)


@mcp.tool
def get_travel_recommendation(location: str, date: str = "tomorrow") -> dict:
    """Generate a simple weather-based travel and packing recommendation.

    This tool applies deterministic thresholds rather than simply echoing the
    raw forecast. It recommends an umbrella when precipitation probability is
    at least 40% (or forecast precipitation is at least 0.05 in), a jacket when
    the low is 55°F or below, heat precautions at 85°F or above, and wind
    caution when gusts reach 30 mph.

    Args:
        location: Human-readable place name.
        date: Target date as YYYY-MM-DD, "today", or "tomorrow".

    Returns:
        The forecast used, boolean recommendation flags, packing suggestions,
        reasons, and the exact thresholds applied.
    """
    try:
        return weather_adapter.get_travel_recommendation(location, date)
    except weather_adapter.WeatherAdapterError as exc:
        return _error(exc)


@mcp.tool
def compare_weather(locations: list[str]) -> dict:
    """Compare today's weather across multiple locations.

    Args:
        locations: Between 2 and 5 human-readable place names.

    Returns:
        A ranked comparison using a simple comfort score that favors
        temperatures near 72°F, lower precipitation probability, and lower
        wind gusts. The score is a project heuristic, not a safety rating.
    """
    try:
        return weather_adapter.compare_locations(locations)
    except weather_adapter.WeatherAdapterError as exc:
        return _error(exc)


if __name__ == "__main__":
    # Databricks Apps route external traffic to the app port. FastMCP's HTTP
    # transport exposes the MCP endpoint at /mcp.
    port = int(os.getenv("DATABRICKS_APP_PORT", os.getenv("PORT", "8000")))
    mcp.run(transport="http", host="0.0.0.0", port=port)
