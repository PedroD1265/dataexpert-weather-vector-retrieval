"""Open-Meteo adapter for the Day 3 Weather MCP server.

All HTTP calls and response parsing live in this module so MCP tool
functions stay thin. Open-Meteo is free for educational/non-commercial
use and requires no API key.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from typing import Any

import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 20

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": "DataExpert-Weather-MCP/1.0 (educational project)",
        "Accept": "application/json",
    }
)


class WeatherAdapterError(RuntimeError):
    """Raised when a location cannot be resolved or the weather API fails."""


WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = _session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise WeatherAdapterError(f"Weather API request failed: {exc}") from exc
    except ValueError as exc:
        raise WeatherAdapterError("Weather API returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise WeatherAdapterError("Weather API returned an unexpected response")
    return payload


@lru_cache(maxsize=128)
def resolve_location(location: str) -> dict[str, Any]:
    """Resolve a human-readable place name to coordinates using Open-Meteo."""
    clean = (location or "").strip()
    if not clean:
        raise WeatherAdapterError("Location is required")

    payload = _request_json(
        GEOCODING_URL,
        {
            "name": clean,
            "count": 1,
            "language": "en",
            "format": "json",
        },
    )
    results = payload.get("results") or []
    if not results:
        raise WeatherAdapterError(f"Could not resolve location: {clean}")

    item = results[0]
    return {
        "query": clean,
        "name": item.get("name"),
        "admin1": item.get("admin1"),
        "country": item.get("country"),
        "country_code": item.get("country_code"),
        "latitude": item.get("latitude"),
        "longitude": item.get("longitude"),
        "timezone": item.get("timezone"),
        "display_name": ", ".join(
            str(value)
            for value in (item.get("name"), item.get("admin1"), item.get("country"))
            if value
        ),
    }


def _weather_label(code: Any) -> str:
    try:
        return WMO_CODES.get(int(code), f"Weather code {code}")
    except (TypeError, ValueError):
        return "Unknown conditions"


def get_current_conditions(location: str) -> dict[str, Any]:
    """Return normalized current conditions for a resolved location."""
    place = resolve_location(location)
    payload = _request_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": (
                "temperature_2m,apparent_temperature,relative_humidity_2m,"
                "precipitation,rain,weather_code,wind_speed_10m,wind_gusts_10m"
            ),
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
        },
    )
    current = payload.get("current") or {}
    units = payload.get("current_units") or {}
    if not current:
        raise WeatherAdapterError("Open-Meteo returned no current conditions")

    return {
        "status": "success",
        "location": place["display_name"],
        "coordinates": {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
        },
        "timezone": payload.get("timezone") or place.get("timezone"),
        "observed_at": current.get("time"),
        "conditions": _weather_label(current.get("weather_code")),
        "weather_code": current.get("weather_code"),
        "temperature_f": current.get("temperature_2m"),
        "feels_like_f": current.get("apparent_temperature"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "precipitation_in": current.get("precipitation"),
        "rain_in": current.get("rain"),
        "wind_mph": current.get("wind_speed_10m"),
        "wind_gust_mph": current.get("wind_gusts_10m"),
        "units": units,
        "provider": "Open-Meteo",
    }


def get_daily_forecast(location: str, days: int = 5) -> dict[str, Any]:
    """Return a normalized daily forecast for 1-7 days."""
    try:
        days = int(days)
    except (TypeError, ValueError) as exc:
        raise WeatherAdapterError("days must be an integer") from exc
    days = max(1, min(days, 7))

    place = resolve_location(location)
    payload = _request_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,precipitation_sum,"
                "wind_speed_10m_max,wind_gusts_10m_max"
            ),
            "forecast_days": days,
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
        },
    )
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    if not dates:
        raise WeatherAdapterError("Open-Meteo returned no daily forecast")

    def value(key: str, index: int) -> Any:
        values = daily.get(key) or []
        return values[index] if index < len(values) else None

    forecast = []
    for index, forecast_date in enumerate(dates):
        code = value("weather_code", index)
        forecast.append(
            {
                "date": forecast_date,
                "conditions": _weather_label(code),
                "weather_code": code,
                "high_f": value("temperature_2m_max", index),
                "low_f": value("temperature_2m_min", index),
                "precipitation_probability_percent": value(
                    "precipitation_probability_max", index
                ),
                "precipitation_in": value("precipitation_sum", index),
                "max_wind_mph": value("wind_speed_10m_max", index),
                "max_gust_mph": value("wind_gusts_10m_max", index),
            }
        )

    return {
        "status": "success",
        "location": place["display_name"],
        "timezone": payload.get("timezone") or place.get("timezone"),
        "days_requested": days,
        "forecast": forecast,
        "provider": "Open-Meteo",
    }


def _normalize_target_date(target_date: str | None) -> str:
    if not target_date or not str(target_date).strip():
        return date.today().isoformat()

    clean = str(target_date).strip().lower()
    if clean == "today":
        return date.today().isoformat()
    if clean == "tomorrow":
        return (date.today() + timedelta(days=1)).isoformat()

    try:
        return date.fromisoformat(clean).isoformat()
    except ValueError as exc:
        raise WeatherAdapterError(
            "date must be YYYY-MM-DD, 'today', or 'tomorrow'"
        ) from exc


def get_travel_recommendation(location: str, target_date: str | None = None) -> dict[str, Any]:
    """Create a deterministic travel/packing recommendation from forecast values."""
    selected_date = _normalize_target_date(target_date)
    forecast_response = get_daily_forecast(location, 7)
    day = next(
        (item for item in forecast_response["forecast"] if item["date"] == selected_date),
        None,
    )
    if day is None:
        raise WeatherAdapterError(
            f"Date {selected_date} is outside the available 7-day forecast window"
        )

    probability = float(day.get("precipitation_probability_percent") or 0)
    precipitation = float(day.get("precipitation_in") or 0)
    high = float(day.get("high_f") or 0)
    low = float(day.get("low_f") or 0)
    gust = float(day.get("max_gust_mph") or 0)
    code = int(day.get("weather_code") or 0)

    umbrella = probability >= 40 or precipitation >= 0.05
    jacket = low <= 55
    heat_precautions = high >= 85
    strong_wind = gust >= 30
    thunderstorm = code in {95, 96, 99}
    wintry = code in {56, 57, 66, 67, 71, 73, 75, 77, 85, 86}

    reasons: list[str] = []
    packing: list[str] = []

    if umbrella:
        packing.append("umbrella or waterproof layer")
        reasons.append(
            f"precipitation chance is {probability:.0f}% with about {precipitation:.2f} in forecast"
        )
    if jacket:
        packing.append("light jacket or warm layer")
        reasons.append(f"forecast low is {low:.0f}°F")
    if heat_precautions:
        packing.append("water and sun/heat protection")
        reasons.append(f"forecast high is {high:.0f}°F")
    if strong_wind:
        reasons.append(f"wind gusts may reach {gust:.0f} mph")
    if thunderstorm:
        reasons.append("thunderstorms are forecast")
    if wintry:
        packing.append("winter-appropriate footwear/layers")
        reasons.append("wintry precipitation is forecast")

    if thunderstorm or wintry:
        outdoor_advice = "use_caution"
    elif strong_wind or probability >= 70:
        outdoor_advice = "use_caution"
    else:
        outdoor_advice = "generally_ok"

    if not reasons:
        reasons.append("no major rain, temperature, or wind thresholds were triggered")
    if not packing:
        packing.append("no special weather gear indicated")

    return {
        "status": "success",
        "location": forecast_response["location"],
        "date": selected_date,
        "forecast": day,
        "recommendation": {
            "umbrella_needed": umbrella,
            "jacket_recommended": jacket,
            "heat_precautions": heat_precautions,
            "strong_wind_caution": strong_wind,
            "outdoor_advice": outdoor_advice,
            "packing": packing,
            "reasons": reasons,
        },
        "logic": {
            "umbrella_threshold": "precipitation probability >= 40% or precipitation >= 0.05 in",
            "jacket_threshold": "forecast low <= 55°F",
            "heat_threshold": "forecast high >= 85°F",
            "wind_threshold": "gusts >= 30 mph",
        },
        "provider": "Open-Meteo",
    }


def compare_locations(locations: list[str]) -> dict[str, Any]:
    """Compare today's forecast across 2-5 locations using a simple comfort score."""
    if not isinstance(locations, list) or not 2 <= len(locations) <= 5:
        raise WeatherAdapterError("locations must contain between 2 and 5 place names")

    comparisons: list[dict[str, Any]] = []
    for location in locations:
        forecast = get_daily_forecast(str(location), 1)
        day = forecast["forecast"][0]
        high = float(day.get("high_f") or 72)
        low = float(day.get("low_f") or 72)
        average_temp = (high + low) / 2
        precip = float(day.get("precipitation_probability_percent") or 0)
        gust = float(day.get("max_gust_mph") or 0)

        score = 100.0
        score -= abs(average_temp - 72.0) * 1.5
        score -= precip * 0.35
        score -= max(0.0, gust - 15.0) * 0.6
        score = round(max(0.0, min(100.0, score)), 1)

        comparisons.append(
            {
                "location": forecast["location"],
                "date": day["date"],
                "conditions": day["conditions"],
                "high_f": day["high_f"],
                "low_f": day["low_f"],
                "precipitation_probability_percent": day[
                    "precipitation_probability_percent"
                ],
                "max_gust_mph": day["max_gust_mph"],
                "comfort_score": score,
            }
        )

    comparisons.sort(key=lambda item: item["comfort_score"], reverse=True)
    return {
        "status": "success",
        "best_location": comparisons[0]["location"],
        "comparison": comparisons,
        "score_explanation": (
            "Higher is better. Score favors temperatures near 72°F, lower precipitation "
            "probability, and lower wind gusts. It is a simple project heuristic, not a safety rating."
        ),
        "provider": "Open-Meteo",
    }
