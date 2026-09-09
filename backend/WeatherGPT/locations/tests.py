"""Tests for location resolution (service, serializers, generic view, error envelope)."""
from unittest.mock import patch

import httpx
from django.test import TestCase
from django.urls import reverse
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


class ReverseGeocodeTests(TestCase):
    def test_reverse_returns_place_name(self):
        service = LocationService(transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={
                "address": {"city": "Jaipur", "state": "Rajasthan", "country": "India"},
                "display_name": "Jaipur, Rajasthan, India",
            })
        ))
        data = service.reverse_geocode(26.9124, 75.7873)
        self.assertEqual(data["name"], "Jaipur")
        self.assertEqual(data["admin1"], "Rajasthan")
        self.assertEqual(data["country"], "India")

    def test_reverse_provider_failure(self):
        service = LocationService(transport=httpx.MockTransport(
            lambda request: httpx.Response(500, text="boom")
        ))
        with self.assertRaises(WeatherProviderError):
            service.reverse_geocode(26.9124, 75.7873)


class SavedLocationEndpointTests(TestCase):
    def setUp(self):
        self.url = reverse("saved-location-list")
        self.key = {"client_key": "test-client-key-123"}

    def _payload(self, **overrides):
        payload = {**self.key, "name": "Jaipur", "country": "India",
                   "latitude": "26.91962", "longitude": "75.78781"}
        payload.update(overrides)
        return payload

    def test_create_list_delete_flow(self):
        create = self.client.post(self.url, self._payload(), content_type="application/json")
        self.assertEqual(create.status_code, 201)

        listing = self.client.get(self.url, self.key)
        self.assertEqual(len(listing.data), 1)
        self.assertEqual(listing.data[0]["name"], "Jaipur")

        detail_url = reverse("saved-location-detail", args=[listing.data[0]["id"]])
        wrong_key = self.client.delete(detail_url + "?client_key=wrong-key-12345")
        self.assertEqual(wrong_key.status_code, 404)

        delete = self.client.delete(detail_url + "?client_key=" + self.key["client_key"])
        self.assertEqual(delete.status_code, 204)
        self.assertEqual(self.client.get(self.url, self.key).data, [])

    def test_client_key_is_required(self):
        response = self.client.post(self.url, {"name": "X"}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_list_without_key_returns_nothing(self):
        self.client.post(self.url, self._payload(), content_type="application/json")
        response = self.client.get(self.url)
        self.assertEqual(response.data, [])


class ReverseGeocodeEndpointTests(TestCase):
    def test_reverse_returns_place_name(self):
        client = APIClient()
        with patch("locations.views.location_service") as service:
            service.reverse_geocode.return_value = {
                "name": "Jaipur",
                "admin1": "Rajasthan",
                "country": "India",
                "latitude": 26.9124,
                "longitude": 75.7873,
            }
            response = client.get(
                "/api/weather/location/reverse/",
                {"latitude": "26.9124", "longitude": "75.7873"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Jaipur")
