"""Chat orchestration.

`understand()` runs the blueprint's core flow:
    user message -> LLM query understanding -> location resolution -> weather retrieval
and returns a grounded structured query ready for the chat endpoint.

Services stay thin and raise shared ApiError types; views contain no logic.
"""
from typing import Optional

from chatbot.llm.provider import llm_service
from chatbot.query import parse_and_validate_query
from common.errors import LocationNotFoundError
from locations.services import location_service
from weather.services import weather_service

MAX_FORECAST_DAYS = 16


class ChatService:
    def __init__(
        self,
        llm=llm_service,
        locations=location_service,
        weather=weather_service,
    ):
        self.llm = llm
        self.locations = locations
        self.weather = weather

    def _resolve_coordinates(self, location_name: str):
        if not location_name:
            # Graceful missing-location: return no coords and let the caller ask for clarification.
            return None
        results = self.locations.search(location_name, count=1)
        if not results:
            raise LocationNotFoundError(location_name)
        return results[0]

    def understand(self, message: str) -> dict:
        raw = self.llm.understand_query(message)
        query = parse_and_validate_query(raw)

        coordinates = self._resolve_coordinates(query["location_name"])
        location = None
        current = None
        daily = None
        if coordinates:
            lat, lon = coordinates["latitude"], coordinates["longitude"]
            location = {
                "name": coordinates["name"] or query["location_name"],
                "latitude": lat,
                "longitude": lon,
            }
            current = self.weather.current(lat, lon, location["name"])
            days = 16 if query["intent"] == "forecast" else 7
            daily = self.weather.forecast(
                lat, lon, days=days, location_name=location["name"]
            )["daily"]

        query["location"] = location
        query["current"] = current["current"] if current else None
        query["daily"] = daily
        return query


# Singleton consumed by the generic views
chat_service = ChatService()