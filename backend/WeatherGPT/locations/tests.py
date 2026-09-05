"""Tests for location resolution (service, serializers, generic view, error envelope)."""
from unittest.mock import patch

import httpx
from django.test import TestCase
from rest_framework.test import APIClient

from common.errors import LocationNotFoundError, WeatherProviderError
from locations.services import LocationService

GEOCODING_PAYLOAD = {
    "results": [
        {
            "name": "Jaipur",
            "country": "India",
            "latitude": 26.91962,
            "longitude": 75.78781,
        },
        {
            "name": "Jaipur",
            "country": "Bangladesh",
            "latitude": 23.858,
            "longitude": 88.644,
        },
    ]
}


def geocoding_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=GEOCODING_PAYLOAD)


def make_location_service(handler=geocoding_handler) -> LocationService:
    return LocationService(transport=httpx.MockTransport(handler))


class LocationServiceTests(TestCase):
    def test_search_normalizes_results(self):
        results = make_location_service().search("Jaipur")
        self.assertEqual(len(results), 2)
        self.assertEqual(
            results[0],
            {"name": "Jaipur", "country": "India", "latitude": 26.91962, "longitude": 75.78781},
        )

    def test_search_empty_results_raises_location_not_found(self):
        service = make_location_service(lambda request: httpx.Response(200, json={}))
        with self.assertRaises(LocationNotFoundError):
            service.search("Atlantis")

    def test_network_error_raises_weather_provider_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("down", request=request)

        with self.assertRaises(WeatherProviderError):
            make_location_service(handler).search("Jaipur")

    def test_http_error_raises_weather_provider_error(self):
        service = make_location_service(lambda request: httpx.Response(500, text="boom"))
        with self.assertRaises(WeatherProviderError):
            service.search("Jaipur")


class LocationEndpointTests(TestCase):
    def test_search_returns_results(self):
        client = APIClient()
        with patch("locations.views.location_service") as service:
            service.search.return_value = GEOCODING_PAYLOAD["results"]
            response = client.get("/api/weather/location/", {"query": "Jaipur"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 2)
        self.assertEqual(response.json()["results"][0]["name"], "Jaipur")

    def test_missing_query_returns_error_envelope(self):
        response = APIClient().get("/api/weather/location/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "INVALID_QUERY")

    def test_unknown_location_returns_error_envelope(self):
        client = APIClient()
        with patch("locations.views.location_service") as service:
            service.search.side_effect = LocationNotFoundError("Atlantis")
            response = client.get("/api/weather/location/", {"query": "Atlantis"})
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body["error"]["code"], "LOCATION_NOT_FOUND")
        self.assertIn("Atlantis", body["error"]["message"])

    def test_provider_failure_returns_error_envelope(self):
        client = APIClient()
        with patch("locations.views.location_service") as service:
            service.search.side_effect = WeatherProviderError()
            response = client.get("/api/weather/location/", {"query": "Jaipur"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "WEATHER_PROVIDER_ERROR")
