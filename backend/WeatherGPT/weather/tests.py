from datetime import date
from unittest.mock import patch

import httpx
from django.test import TestCase
from rest_framework.test import APIClient

from weather.providers.base import WeatherProvider
from weather.providers.open_meteo import OpenMeteoError, OpenMeteoProvider
from weather.services import WeatherService

from common.errors import WeatherProviderError

CURRENT_PAYLOAD = {
    "latitude": 26.9124,
    "longitude": 75.7873,
    "current": {
        "time": "2026-09-06T11:30",
        "temperature_2m": 31.2,
        "relative_humidity_2m": 61,
        "apparent_temperature": 34.0,
        "precipitation": 0.0,
        "wind_speed_10m": 14.2,
        "weather_code": 2,
    },
}

FORECAST_PAYLOAD = {
    "latitude": 26.9124,
    "longitude": 75.7873,
    "daily": {
        "time": ["2026-09-06", "2026-09-07", "2026-09-08"],
        "weather_code": [2, 61, 63],
        "temperature_2m_max": [34.5, 33.0, 31.2],
        "temperature_2m_min": [26.1, 25.0, 24.0],
        "precipitation_sum": [0.0, 4.2, 7.0],
        "precipitation_probability_max": [0, 65, 80],
        "wind_speed_10m_max": [12.5, 18.0, 22.4],
    },
}


HOURLY_PAYLOAD = {
    "hourly": {
        "time": ["2026-09-07T10:00", "2026-09-07T11:00", "2026-09-07T12:00"],
        "temperature_2m": [21.0, 22.5, 24.0],
        "precipitation_probability": [10, 20, 30],
        "precipitation": [0.0, 0.1, 0.2],
        "weather_code": [1, 2, 61],
        "wind_speed_10m": [8.0, 9.5, 11.0],
    }
}


def open_meteo_handler(request: httpx.Request) -> httpx.Response:
    """Fake Open-Meteo backend switching on the requested params."""
    params = dict(request.url.params)
    if "current" in params:
        return httpx.Response(200, json=CURRENT_PAYLOAD)
    if "daily" in params:
        return httpx.Response(200, json=FORECAST_PAYLOAD)
    if "hourly" in params:
        return httpx.Response(200, json=HOURLY_PAYLOAD)
    return httpx.Response(404, text="not found")


def make_provider(handler=open_meteo_handler) -> OpenMeteoProvider:
    return OpenMeteoProvider(transport=httpx.MockTransport(handler))


class ProviderInterfaceTests(TestCase):
    def test_abstract_class_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            WeatherProvider()

    def test_get_current_weather_returns_parsed_payload(self):
        self.assertEqual(make_provider().get_current_weather(26.9124, 75.7873), CURRENT_PAYLOAD)

    def test_get_forecast_returns_parsed_payload(self):
        provider = make_provider()
        start, end = date(2026, 9, 6), date(2026, 9, 8)
        self.assertEqual(provider.get_forecast(26.9124, 75.7873, start, end), FORECAST_PAYLOAD)

    def test_get_forecast_sends_date_params(self):
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured.update(dict(request.url.params))
            return httpx.Response(200, json=FORECAST_PAYLOAD)

        provider = make_provider(handler)
        provider.get_forecast(26.9124, 75.7873, date(2026, 9, 6), date(2026, 9, 8))
        self.assertEqual(captured["start_date"], "2026-09-06")
        self.assertEqual(captured["end_date"], "2026-09-08")

    def test_network_error_raises_open_meteo_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        with self.assertRaises(OpenMeteoError):
            make_provider(handler).get_current_weather(26.9124, 75.7873)

    def test_http_error_raises_open_meteo_error(self):
        provider = make_provider(lambda request: httpx.Response(500, text="boom"))
        with self.assertRaises(OpenMeteoError):
            provider.get_current_weather(26.9124, 75.7873)
class ServiceNormalizationTests(TestCase):
    def setUp(self):
        self.service = WeatherService(make_provider())

    def test_current_matches_internal_model(self):
        data = self.service.current(26.9124, 75.7873, location_name="Jaipur")
        self.assertEqual(
            data["location"], {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873}
        )
        self.assertEqual(
            data["current"],
            {
                "temperature_c": 31.2,
                "feels_like_c": 34.0,
                "humidity_pct": 61,
                "wind_kmh": 14.2,
                "precipitation_mm": 0.0,
                "condition": "Partly cloudy",
            },
        )

    def test_forecast_normalizes_each_day(self):
        data = self.service.forecast(26.9124, 75.7873, location_name="Jaipur")
        self.assertEqual(len(data["daily"]), 3)
        self.assertEqual(data["daily"][0]["date"], "2026-09-06")
        self.assertEqual(data["daily"][1]["condition"], "Light rain")
        self.assertEqual(data["daily"][2]["precipitation_probability_pct"], 80)

    def test_forecast_rejects_days_out_of_range(self):
        with self.assertRaises(ValueError):
            self.service.forecast(26.9124, 75.7873, days=0)
        with self.assertRaises(ValueError):
            self.service.forecast(26.9124, 75.7873, days=17)

    def test_provider_error_propagates(self):
        broken = WeatherService(make_provider(lambda request: httpx.Response(500, text="boom")))
        with self.assertRaises(WeatherProviderError):
            broken.current(26.9124, 75.7873)

    def test_hourly_normalizes_entries(self):
        data = self.service.hourly(26.9124, 75.7873, location_name="Jaipur")
        self.assertEqual(len(data["hourly"]), 3)
        self.assertEqual(data["hourly"][0]["temperature_c"], 21.0)
        self.assertEqual(data["hourly"][2]["condition"], "Light rain")

    def test_hourly_rejects_hours_out_of_range(self):
        with self.assertRaises(ValueError):
            self.service.hourly(26.9124, 75.7873, hours=0)
        with self.assertRaises(ValueError):
            self.service.hourly(26.9124, 75.7873, hours=49)

    def test_compare_returns_both_cities(self):
        with patch("weather.services.location_service.search", return_value=[
            {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873}
        ]):
            data = self.service.compare("Jaipur", "Delhi")
        self.assertEqual(len(data["comparison"]), 2)
        self.assertEqual(data["comparison"][0]["current"]["temperature_c"], 31.2)
        self.assertEqual(data["comparison"][0]["location"]["name"], "Jaipur")


class WeatherEndpointTests(TestCase):
    def test_current_returns_normalized_data(self):
        client = APIClient()
        with patch("weather.views.weather_service") as service:
            service.current.return_value = {
                "location": {"name": None, "latitude": 26.9124, "longitude": 75.7873},
                "current": {"temperature_c": 31.2},
            }
            response = client.get(
                "/api/weather/current/", {"latitude": "26.9124", "longitude": "75.7873"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["current"]["temperature_c"], 31.2)

    def test_current_rejects_invalid_coordinates(self):
        response = APIClient().get(
            "/api/weather/current/", {"latitude": "999", "longitude": "75.7873"}
        )
        self.assertEqual(response.status_code, 400)

    def test_forecast_returns_normalized_data(self):
        client = APIClient()
        with patch("weather.views.weather_service") as service:
            service.forecast.return_value = {"location": {"name": None}, "daily": []}
            response = client.get(
                "/api/weather/forecast/",
                {"latitude": "26.9124", "longitude": "75.7873", "days": "7"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["daily"], [])

    def test_forecast_rejects_days_out_of_range(self):
        response = APIClient().get(
            "/api/weather/forecast/",
            {"latitude": "26.9124", "longitude": "75.7873", "days": "99"},
        )
        self.assertEqual(response.status_code, 400)

    def test_hourly_returns_normalized_data(self):
        client = APIClient()
        with patch("weather.views.weather_service") as service:
            service.hourly.return_value = {"location": {"name": None}, "hourly": []}
            response = client.get(
                "/api/weather/hourly/",
                {"latitude": "26.9124", "longitude": "75.7873", "hours": "12"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["hourly"], [])

    def test_hourly_rejects_hours_out_of_range(self):
        response = APIClient().get(
            "/api/weather/hourly/",
            {"latitude": "26.9124", "longitude": "75.7873", "hours": "99"},
        )
        self.assertEqual(response.status_code, 400)

    def test_compare_returns_both_cities(self):
        client = APIClient()
        with patch("weather.views.weather_service") as service:
            service.compare.return_value = {"comparison": [{}, {}]}
            response = client.get(
                "/api/weather/compare/", {"city1": "Jaipur", "city2": "Delhi"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["comparison"]), 2)
