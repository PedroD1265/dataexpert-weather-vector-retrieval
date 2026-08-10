"""Public weather API client used by POST /weather/sync.

Weather content comes from the U.S. National Weather Service (NWS).
Open-Meteo Geocoding is used only to resolve a city/state string to lat/lon.
No API keys are required.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import requests

OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
NWS_BASE_URL = "https://api.weather.gov"

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


class WeatherClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedLocation:
    requested: str
    display_name: str
    latitude: float
    longitude: float


class WeatherClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": os.environ.get(
                "NWS_USER_AGENT",
                "DataExpertWeatherVectorHomework/1.0 (github.com/PedroD1265/dataexpert-weather-vector-retrieval)",
            ),
            "Accept": "application/geo+json, application/json",
        })

    def _get_json(self, url: str, *, params: dict | None = None) -> dict:
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise WeatherClientError(f"Weather API request failed: {exc}") from exc
        except ValueError as exc:
            raise WeatherClientError(f"Weather API returned invalid JSON from {url}") from exc

    def resolve_location(self, location: str) -> ResolvedLocation:
        """Resolve 'Chicago, IL' style input using Open-Meteo Geocoding."""
        parts = [part.strip() for part in location.split(",") if part.strip()]
        city = parts[0] if parts else location.strip()
        state_hint = parts[1].upper() if len(parts) > 1 else None
        desired_state = STATE_NAMES.get(state_hint, state_hint) if state_hint else None

        data = self._get_json(
            OPEN_METEO_GEOCODING_URL,
            params={"name": city, "count": 10, "language": "en", "format": "json"},
        )
        results = data.get("results") or []
        if not results:
            raise WeatherClientError(f"Could not resolve location: {location}")

        us_results = [r for r in results if r.get("country_code") == "US"]
        candidates = us_results or results

        if desired_state:
            state_matches = [
                r for r in candidates
                if str(r.get("admin1", "")).lower() == str(desired_state).lower()
            ]
            if state_matches:
                candidates = state_matches

        best = candidates[0]
        latitude = best.get("latitude")
        longitude = best.get("longitude")
        if latitude is None or longitude is None:
            raise WeatherClientError(f"Resolved location has no coordinates: {location}")

        display_parts = [best.get("name")]
        if best.get("admin1"):
            display_parts.append(best["admin1"])
        if best.get("country_code"):
            display_parts.append(best["country_code"])

        return ResolvedLocation(
            requested=location,
            display_name=", ".join(str(x) for x in display_parts if x),
            latitude=float(latitude),
            longitude=float(longitude),
        )

    def _nws_point(self, resolved: ResolvedLocation) -> dict:
        lat = round(resolved.latitude, 4)
        lon = round(resolved.longitude, 4)
        return self._get_json(f"{NWS_BASE_URL}/points/{lat},{lon}")

    def fetch_forecast_documents(
        self,
        resolved: ResolvedLocation,
        point_data: dict,
    ) -> list[dict]:
        forecast_url = (point_data.get("properties") or {}).get("forecast")
        if not forecast_url:
            raise WeatherClientError(
                f"NWS did not provide a forecast URL for {resolved.display_name}"
            )

        forecast = self._get_json(forecast_url)
        properties = forecast.get("properties") or {}
        generated_at = properties.get("generatedAt") or properties.get("updateTime")
        documents = []

        for period in properties.get("periods") or []:
            narrative = (period.get("detailedForecast") or period.get("shortForecast") or "").strip()
            if not narrative:
                continue

            stable_key = "|".join([
                "forecast",
                resolved.display_name,
                str(period.get("startTime") or ""),
                str(period.get("name") or period.get("number") or ""),
            ])
            document_id = "forecast_" + hashlib.sha256(stable_key.encode("utf-8")).hexdigest()

            documents.append({
                "id": document_id,
                "location": resolved.display_name,
                "source_type": "forecast",
                "headline": period.get("name") or period.get("shortForecast") or "Forecast",
                "narrative_text": narrative,
                "issued_at": generated_at,
                "effective_at": period.get("startTime"),
                "payload": period,
            })

        return documents

    def fetch_alert_documents(self, resolved: ResolvedLocation) -> list[dict]:
        lat = round(resolved.latitude, 4)
        lon = round(resolved.longitude, 4)
        data = self._get_json(
            f"{NWS_BASE_URL}/alerts/active",
            params={"point": f"{lat},{lon}"},
        )

        documents = []
        for feature in data.get("features") or []:
            props = feature.get("properties") or {}
            description = (props.get("description") or "").strip()
            instruction = (props.get("instruction") or "").strip()

            narrative_parts = []
            if description:
                narrative_parts.append(description)
            if instruction:
                narrative_parts.append(f"Instructions: {instruction}")
            narrative = "\n\n".join(narrative_parts).strip()
            if not narrative:
                continue

            raw_id = feature.get("id") or props.get("id")
            if raw_id:
                document_id = "alert_" + hashlib.sha256(str(raw_id).encode("utf-8")).hexdigest()
            else:
                stable_key = "|".join([
                    "alert",
                    resolved.display_name,
                    str(props.get("event") or ""),
                    str(props.get("effective") or props.get("onset") or ""),
                ])
                document_id = "alert_" + hashlib.sha256(stable_key.encode("utf-8")).hexdigest()

            documents.append({
                "id": document_id,
                "location": resolved.display_name,
                "source_type": "alert",
                "headline": props.get("headline") or props.get("event") or "Weather Alert",
                "narrative_text": narrative,
                "issued_at": props.get("sent") or props.get("onset"),
                "effective_at": props.get("effective") or props.get("onset"),
                "payload": feature,
            })

        return documents

    def harvest_location(self, location: str, limit: int = 50) -> list[dict]:
        """Resolve one location and return normalized alert + forecast docs."""
        resolved = self.resolve_location(location)
        point_data = self._nws_point(resolved)

        alerts = self.fetch_alert_documents(resolved)
        forecasts = self.fetch_forecast_documents(resolved, point_data)
        documents = alerts + forecasts
        return documents[:limit]
