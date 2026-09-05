"""Weather provider contract.

Application code depends on this interface, never on a concrete provider
(Strategy pattern, implementation.md section 18).
"""
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