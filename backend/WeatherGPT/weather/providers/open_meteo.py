"""Open-Meteo weather provider.

Free weather API (no key required). All Open-Meteo-specific HTTP calls and
response parsing live here; the rest of the app only sees normalized data.
"""
import httpx
from datetime import date
from typing import Any, Dict, Optional

from weather.providers.base import WeatherProvider

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
HTTP_TIMEOUT_SECONDS = 10.0

CURRENT_PARAMS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,"
    "precipitation,wind_speed_10m,weather_code"
)
DAILY_PARAMS = (
    "weather_code,temperature_2m_max,temperature_2m_min,"
    "precipitation_sum,precipitation_probability_max,wind_speed_10m_max"
)
HOURLY_PARAMS = (
    "temperature_2m,precipitation_probability,precipitation,"
    "weather_code,wind_speed_10m"
)


class OpenMeteoError(Exception):
    """Raised when Open-Meteo cannot be reached or returns unusable data."""


class OpenMeteoProvider(WeatherProvider):
    def __init__(
        self,
        base_url: str = OPEN_METEO_BASE_URL,
        timeout: float = HTTP_TIMEOUT_SECONDS,
        transport: Optional[httpx.BaseTransport] = None,
    ):
        self.base_url = base_url
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": CURRENT_PARAMS,
            "timezone": "auto",
        }
        return self._get(params)

    def get_hourly_forecast(
        self,
        latitude: float,
        longitude: float,
        hours: int = 24,
    ) -> Dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": HOURLY_PARAMS,
            "forecast_hours": hours,
            "timezone": "auto",
        }
        return self._get(params)

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": DAILY_PARAMS,
            "timezone": "auto",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        return self._get(params)

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self._client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise OpenMeteoError(f"Open-Meteo request failed: {exc}") from exc

    def close(self) -> None:
        self._client.close()