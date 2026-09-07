"""Chat orchestration.

`understand()` and `process_message()` run the blueprint's core flow:
    user message -> LLM query understanding -> location resolution -> weather retrieval
    -> grounded prompt -> LLM generation -> response

Services stay thin and raise shared ApiError types; views contain no logic.
"""
import threading
import time
from datetime import date
from typing import Optional

from chatbot.llm.provider import llm_service
from chatbot.prompts import SYSTEM_PROMPT, build_weather_context
from chatbot.query import parse_and_validate_query
from common.errors import LocationNotFoundError, RateLimitedError
from locations.services import location_service
from weather.services import weather_service

MAX_FORECAST_DAYS = 16
RATE_LIMIT_MAX = 10  # requests
RATE_LIMIT_WINDOW_SECONDS = 60.0


class SlidingWindowRateLimiter:
    """Simple in-memory sliding-window limiter keyed by IP (no external dep)."""

    def __init__(self, max_requests: int = RATE_LIMIT_MAX, window_seconds: float = RATE_LIMIT_WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            window_start = now - self.window_seconds
            timestamps = [t for t in self._hits.get(key, []) if t > window_start]
            if len(timestamps) >= self.max_requests:
                self._hits[key] = timestamps
                return False
            timestamps.append(now)
            self._hits[key] = timestamps
            return True


class ChatService:
    def __init__(
        self,
        llm=llm_service,
        locations=location_service,
        weather=weather_service,
        rate_limiter=None,
    ):
        self.llm = llm
        self.locations = locations
        self.weather = weather
        self.rate_limiter = rate_limiter or SlidingWindowRateLimiter()

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

    def process_message(self, message: str, client_ip: str = "") -> dict:
        """Full blueprint vertical slice (implementation.md section 19)."""
        if not self.rate_limiter.allow(client_ip):
            raise RateLimitedError()

        query = self.understand(message)

        if query["location"] is None:
            # No locatable place -> LLM asks for clarification instead of inventing facts.
            discovered = query.get("language", "en")
            response_text = self.llm.generate(
                SYSTEM_PROMPT,
                "The user asked for weather but no location was detected. "
                "Ask for the location/city in the user's language.",
            )
            return {
                "answer": response_text,
                "language": discovered,
                "needs_location": True,
                "intent": query["intent"],
                "location": None,
                "weather_context": None,
            }

        grounded = build_weather_context(
            location=query["location"],
            current=query["current"],
            forecast_daily=query["daily"],
        )
        user_content = (
            f"{grounded}\n\nQUESTION: {message}\n"
            "Answer in the same language as the question. Be concise, practical, "
            "and actionable. Do not invent any weather facts."
        )
        answer = self.llm.generate(SYSTEM_PROMPT, user_content)

        return {
            "answer": answer,
            "language": query.get("language", "en"),
            "needs_location": False,
            "intent": query["intent"],
            "location": query["location"],
            "weather_context": {
                "current": query["current"],
                "forecast_daily": query["daily"],
            },
        }


# Singleton consumed by the generic views
chat_service = ChatService()