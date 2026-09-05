from datetime import date, timedelta
from typing import Any, Dict, Optional

from weather.providers.base import WeatherProvider
from weather.providers.open_meteo import OpenMeteoProvider
from weather.wmo import condition_for

MAX_FORECAST_DAYS = 16


class WeatherService:
    def __init__(self, provider: WeatherProvider):
        self.provider = provider

    def current(
        self,
        latitude: float,
        longitude: float,
        location_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        raw = self.provider.get_current_weather(latitude, longitude)
        current = raw["current"]
        return {
            "location": {
                "name": location_name,
                "latitude": latitude,
                "longitude": longitude,
            },
            "current": {
                "temperature_c": current["temperature_2m"],
                "feels_like_c": current["apparent_temperature"],
                "humidity_pct": current["relative_humidity_2m"],
                "wind_kmh": current["wind_speed_10m"],
                "precipitation_mm": current["precipitation"],
                "condition": condition_for(current["weather_code"]),
            },
        }

    def forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        location_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not 1 <= days <= MAX_FORECAST_DAYS:
            raise ValueError("days must be between 1 and 16")

        start_date = date.today()
        end_date = start_date + timedelta(days=days - 1)
        raw = self.provider.get_forecast(latitude, longitude, start_date, end_date)
        daily = raw["daily"]

        forecasts = [
            {
                "date": daily["time"][i],
                "temperature_max_c": daily["temperature_2m_max"][i],
                "temperature_min_c": daily["temperature_2m_min"][i],
                "precipitation_probability_pct": daily["precipitation_probability_max"][i],
                "precipitation_mm": daily["precipitation_sum"][i],
                "condition": condition_for(daily["weather_code"][i]),
            }
            for i in range(len(daily["time"]))
        ]

        return {
            "location": {
                "name": location_name,
                "latitude": latitude,
                "longitude": longitude,
            },
            "daily": forecasts,
        }


# Singleton consumed by the generic views
weather_service = WeatherService(OpenMeteoProvider())