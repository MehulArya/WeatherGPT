"""Location resolution via the Open-Meteo Geocoding API.

Normalizes results into {name, country, latitude, longitude} and raises
shared ApiError types so the HTTP layer stays a thin generic view.
"""
import httpx

from common.errors import LocationNotFoundError, WeatherProviderError

GEOCODING_BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"
REVERSE_GEOCODE_BASE_URL = "https://nominatim.openstreetmap.org/reverse"
REVERSE_HEADERS = {"User-Agent": "WeatherGPT/0.1 (weather demo)"}
HTTP_TIMEOUT_SECONDS = 10.0


class LocationService:
    def __init__(
        self,
        base_url: str = GEOCODING_BASE_URL,
        timeout: float = HTTP_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport = None,
    ):
        self.base_url = base_url
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def search(self, query: str, count: int = 5) -> list:
        params = {
            "name": query,
            "count": count,
            "language": "en",
            "format": "json",
        }
        try:
            response = self._client.get(self.base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise WeatherProviderError() from exc

        results = payload.get("results", [])
        if not results:
            raise LocationNotFoundError(query)

        return [
            {
                "name": item.get("name"),
                "country": item.get("country"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
            }
            for item in results
        ]

    def reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """Turn coordinates into the nearest place name (OpenStreetMap/Nominatim)."""
        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "zoom": 10,
            "accept-language": "en",
        }
        try:
            response = self._client.get(
                REVERSE_GEOCODE_BASE_URL, params=params, headers=REVERSE_HEADERS
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise WeatherProviderError() from exc

        address = payload.get("address", {})
        name = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
            or (payload.get("display_name", "").split(",")[0].strip())
        )
        return {
            "name": name or "Unknown place",
            "admin1": address.get("state", ""),
            "country": address.get("country", ""),
            "latitude": latitude,
            "longitude": longitude,
        }

    def close(self) -> None:
        self._client.close()


# Singleton consumed by the generic view
location_service = LocationService()