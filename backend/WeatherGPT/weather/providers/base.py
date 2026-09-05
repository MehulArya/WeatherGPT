from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict


class WeatherProvider(ABC):
    """Interface every weather source must implement."""

    @abstractmethod
    def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Return current-weather data for the given coordinates."""
        raise NotImplementedError

    @abstractmethod
    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Return daily forecast data between start_date and end_date."""
        raise NotImplementedError