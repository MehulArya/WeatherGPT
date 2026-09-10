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
from chatbot.models import Conversation, Message
from chatbot.prompts import SYSTEM_PROMPT, build_weather_context
from chatbot.query import parse_and_validate_query
from common.errors import LocationNotFoundError, RateLimitedError
from locations.services import location_service
from weather.services import weather_service

try:
    from alerts.services import AlertEngine
except Exception:  # alerts app unavailable in some test setups
    AlertEngine = None

MAX_FORECAST_DAYS = 16
RATE_LIMIT_MAX = 10  # requests
RATE_LIMIT_WINDOW_SECONDS = 60.0

HOURLY_DATE_REFERENCES = {"today", "tonight", "now", "this evening"}
HOURLY_MESSAGE_TRIGGERS = ("hour", "hourly", "tonight", "this evening")


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
        alerts_engine=None,
    ):
        self.llm = llm
        self.locations = locations
        self.weather = weather
        self.rate_limiter = rate_limiter or SlidingWindowRateLimiter()
        self._alerts_engine_override = alerts_engine

    def _resolve_coordinates(self, location_name: str):
        if not location_name:
            # Graceful missing-location: return no coords and let the caller ask for clarification.
            return None
        results = self.locations.search(location_name, count=1)
        if not results:
            raise LocationNotFoundError(location_name)
        return results[0]

    @property
    def _alerts_engine(self):
        if "_alerts_engine_instance" not in self.__dict__:
            override = self.__dict__.get("_alerts_engine_override")
            engine = override if override is not None else (AlertEngine() if AlertEngine else None)
            self.__dict__["_alerts_engine_instance"] = engine
        return self.__dict__["_alerts_engine_instance"]

    def _wants_hourly(self, message: str, query: dict) -> bool:
        lowered = message.lower()
        return (
            query.get("date_reference", "").strip().lower() in HOURLY_DATE_REFERENCES
            or any(trigger in lowered for trigger in HOURLY_MESSAGE_TRIGGERS)
        )

    def understand(self, message: str, location_context: dict = None, units: str = None) -> dict:
        raw = self.llm.understand_query(message)
        query = parse_and_validate_query(raw)
        # Explicit ?units= / body units wins over LLM auto-detection.
        if units in ("metric", "imperial"):
            query["units"] = units
        effective_units = query["units"]
        intent = query["intent"]

        if intent == "comparison":
            return self._understand_comparison(query, units=effective_units)

        coordinates = self._resolve_coordinates(query["location_name"])
        location = None
        current = None
        daily = None
        hourly = None
        alerts = None
        if coordinates:
            lat, lon = coordinates["latitude"], coordinates["longitude"]
            location = {
                "name": coordinates["name"] or query["location_name"],
                "latitude": lat,
                "longitude": lon,
            }
            current = self.weather.current(lat, lon, location["name"], units=effective_units)
            days = 16 if intent == "forecast" else 7
            daily = self.weather.forecast(
                lat, lon, days=days, location_name=location["name"], units=effective_units
            )["daily"]
            if intent in ("advisory", "alert"):
                alerts = self._alerts_engine.evaluate_forecast(
                    lat, lon, location["name"], daily
                )
            if self._wants_hourly(message, query):
                hourly = self.weather.hourly(lat, lon, hours=12, units=effective_units)["hourly"]
        elif location_context:
            # Follow-up question ("What about tomorrow?") reuses the prior location.
            lat, lon = location_context["latitude"], location_context["longitude"]
            location = location_context
            current = self.weather.current(lat, lon, location["name"], units=effective_units)
            days = 16 if intent == "forecast" else 7
            daily = self.weather.forecast(
                lat, lon, days=days, location_name=location["name"], units=effective_units
            )["daily"]
            if intent in ("advisory", "alert"):
                alerts = self._alerts_engine.evaluate_forecast(
                    lat, lon, location["name"], daily
                )
            if self._wants_hourly(message, query):
                hourly = self.weather.hourly(lat, lon, hours=12, units=effective_units)["hourly"]

        query["location"] = location
        query["current"] = current["current"] if current else None
        query["daily"] = daily
        query["hourly"] = hourly
        query["comparison"] = None
        query["alerts"] = alerts
        return query

    def _understand_comparison(self, query: dict, units: str = "metric") -> dict:
        """Resolve both cities for a comparison intent; clarify if either is missing."""
        first_coord = self._resolve_coordinates(query["location_name"])
        second_coord = self._resolve_coordinates(query.get("secondary_location_name", ""))
        if first_coord is None or second_coord is None:
            query["location"] = None
            query["current"] = None
            query["daily"] = None
            query["hourly"] = None
            query["comparison"] = None
            query["alerts"] = None
            return query
        comparison = []
        primary = None
        names = (query["location_name"], query.get("secondary_location_name", ""))
        for coords, fallback_name in zip((first_coord, second_coord), names):
            entry = self.weather.current(
                coords["latitude"], coords["longitude"], coords["name"], units=units
            )
            entry["location"]["name"] = coords["name"] or fallback_name
            comparison.append(entry)
            if primary is None:
                primary = dict(entry["location"])
        query["location"] = primary
        query["current"] = comparison[0]["current"]
        query["daily"] = None
        query["hourly"] = None
        query["comparison"] = {"entries": comparison, "secondary_location": second_coord["name"]}
        query["alerts"] = None
        return query

    def _get_or_create_conversation(self, conversation_id, message):
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass
        return Conversation.objects.create(title=message[:100] or "New conversation")

    def _last_location(self, conversation):
        for msg in conversation.messages.order_by("-created_at")[:20]:
            location = msg.metadata.get("location")
            if location:
                return location
        return None

    def _message_history(self, conversation, max_turns=6):
        return "\n".join(
            f"{m.role}: {m.content}"
            for m in conversation.messages.order_by("created_at")[:max_turns]
        )

    def _save_message(self, conversation, role, content, **metadata):
        Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            metadata=metadata,
        )

    def process_message(self, message: str, conversation_id: int = None, client_ip: str = "", units: str = None) -> dict:
        """Full blueprint vertical slice (implementation.md section 19) with persistence."""
        if not self.rate_limiter.allow(client_ip):
            raise RateLimitedError()

        conversation = self._get_or_create_conversation(conversation_id, message)
        history = self._message_history(conversation)
        query = self.understand(
            message,
            location_context=self._last_location(conversation),
            units=units,
        )
        effective_units = query.get("units", "metric")

        self._save_message(
            conversation,
            "user",
            message,
            intent=query["intent"],
            location=query["location"],
            date_reference=query.get("date_reference", ""),
            language=query.get("language", "en"),
            units=effective_units,
        )

        if query["location"] is None:
            # Comparison with no resolvable city still needs both names present.
            comparison_missing = (
                query["comparison"] is not None and query["comparison"].get("secondary_location") is None
            )
            if not comparison_missing:
                # No locatable place -> LLM asks for clarification instead of inventing facts.
                discovered = query.get("language", "en")
                language_line = "English" if discovered != "hi" else "Hindi (Devanagari script)"
                response_text = self.llm.generate(
                    SYSTEM_PROMPT,
                    "The user asked for weather but no location was detected. "
                    f"Ask for the location/city in {language_line}.",
                )
                self._save_message(conversation, "assistant", response_text, intent=query["intent"])
                conversation.save()  # bump updated_at
                return {
                    "conversation_id": conversation.id,
                    "answer": response_text,
                    "language": discovered,
                    "needs_location": True,
                    "intent": query["intent"],
                    "location": None,
                    "weather_context": None,
                }

        grounded = build_weather_context(
            location=query["location"] or {"name": None, "latitude": None, "longitude": None},
            current=query["current"],
            forecast_daily=query["daily"],
            hourly=query["hourly"],
            comparison=(query["comparison"] or {}).get("entries"),
            alerts=query["alerts"],
            units=effective_units,
        )
        intent_guidance = ""
        if query["intent"] in ("advisory",):
            intent_guidance = (
                " Give practical advice: clothing, umbrella, and travel guidance "
                "grounded only in the weather context."
            )
        elif query["intent"] in ("alert",):
            intent_guidance = (
                " Clearly state whether any prototype alert fired. Emphasize this is "
                "general guidance, not an official meteorological warning."
            )
        elif query["intent"] in ("comparison",):
            intent_guidance = (
                " Compare both cities directly using the Comparison block and name "
                "the warmer/colder/wetter city explicitly."
            )
        language_line = (
            "Hindi (Devanagari script)" if query.get("language") == "hi"
            else "the same language as the question"
        )
        user_content = (
            f"{grounded}\n\nCONVERSATION HISTORY:\n{history}\n\nQUESTION: {message}\n"
            f"Answer in {language_line}. Be concise, practical, "
            f"and actionable. Do not invent any weather facts.{intent_guidance}"
        )
        answer = self.llm.generate(SYSTEM_PROMPT, user_content)
        self._save_message(conversation, "assistant", answer, intent=query["intent"])
        conversation.save()  # bump updated_at

        weather_context = {
            "current": query["current"],
            "forecast_daily": query["daily"],
            "units": effective_units,
        }
        if query["hourly"] is not None:
            weather_context["hourly"] = query["hourly"]
        if query["comparison"] is not None:
            weather_context["comparison"] = query["comparison"]["entries"]
            weather_context["units"] = effective_units
        if query["alerts"]:
            weather_context["alerts"] = [
                {
                    "alert_type": getattr(a, "alert_type", None) if not isinstance(a, dict) else a.get("alert_type"),
                    "severity": getattr(a, "severity", None) if not isinstance(a, dict) else a.get("severity"),
                    "title": getattr(a, "title", None) if not isinstance(a, dict) else a.get("title"),
                    "description": getattr(a, "description", None) if not isinstance(a, dict) else a.get("description"),
                    "advice": getattr(a, "advice", None) if not isinstance(a, dict) else a.get("advice"),
                }
                for a in query["alerts"]
            ]

        return {
            "conversation_id": conversation.id,
            "answer": answer,
            "language": query.get("language", "en"),
            "units": effective_units,
            "needs_location": False,
            "intent": query["intent"],
            "location": query["location"],
            "weather_context": weather_context,
        }


# Singleton consumed by the generic views
chat_service = ChatService()