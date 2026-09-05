"""Location resolution via the Open-Meteo Geocoding API.

Normalizes results into {name, country, latitude, longitude} and raises
shared ApiError types so the HTTP layer stays a thin generic view.
"""
import httpx

from common.errors import LocationNotFoundError, WeatherProviderError

GEOCODING_BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"
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

    def close(self) -> None:
        self._client.close()


# Singleton consumed by the generic view
location_service = LocationService()