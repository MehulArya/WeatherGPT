"""Tests for the chat layer (LLM provider, schema validation, ChatService, endpoints)."""
from unittest.mock import patch

from django.test import TestCase

from chatbot.models import Conversation, Message
from chatbot.query import parse_and_validate_query
from chatbot.services import ChatService, SlidingWindowRateLimiter

VALID_QUERY = {
    "intent": "forecast",
    "location_name": "Jaipur",
    "date_reference": "tomorrow",
    "language": "en",
    "weather_parameters": ["precipitation"],
}

FULL_CURRENT = {
    "current": {
        "temperature_c": 31.2,
        "feels_like_c": 34.0,
        "humidity_pct": 61,
        "wind_kmh": 14.2,
        "precipitation_mm": 0.0,
        "condition": "Partly cloudy",
    }
}

FULL_DAY = {
    "date": "2026-09-06",
    "temperature_max_c": 34.5,
    "temperature_min_c": 26.1,
    "precipitation_probability_pct": 65,
    "precipitation_mm": 4.2,
    "condition": "Rain showers",
}


class FakeLLM:
    def __init__(self, output=None, understand_output=None, generate_output=None):
        # `output` keeps backward compat with Phase 4 tests (dict understood output)
        self.understand_output = understand_output or output or VALID_QUERY
        self.generate_output = generate_output or "It will rain in Jaipur tomorrow."
        self.generated_prompts = []

    def understand_query(self, message: str):
        return self.understand_output

    def generate(self, system_prompt: str, user_content: str, json_mode=False):
        self.generated_prompts.append(user_content)
        return self.generate_output


class SchemaValidationTests(TestCase):
    def test_accepts_valid_query(self):
        self.assertEqual(parse_and_validate_query(VALID_QUERY), {
            "intent": "forecast",
            "location_name": "Jaipur",
            "secondary_location_name": "",
            "date_reference": "tomorrow",
            "language": "en",
            "units": "metric",
            "weather_parameters": ["precipitation"],
        })

    def test_accepts_json_string(self):
        import json
        self.assertEqual(
            parse_and_validate_query(json.dumps(VALID_QUERY)),
            parse_and_validate_query(VALID_QUERY),
        )

    def test_rejects_invalid_intent(self):
        bad = dict(VALID_QUERY, intent="poop")
        with self.assertRaises(Exception):
            parse_and_validate_query(bad)

    def test_rejects_unknown_weather_parameter(self):
        bad = dict(VALID_QUERY, weather_parameters=["tornadoes"])
        with self.assertRaises(Exception):
            parse_and_validate_query(bad)

    def test_rejects_empty_parameters(self):
        bad = dict(VALID_QUERY, weather_parameters=[])
        with self.assertRaises(Exception):
            parse_and_validate_query(bad)

    def test_rejects_invalid_units(self):
        bad = dict(VALID_QUERY, units="kelvin")
        with self.assertRaises(Exception):
            parse_and_validate_query(bad)

    def test_rejects_overlong_secondary_location(self):
        bad = dict(VALID_QUERY, secondary_location_name="x" * 101)
        with self.assertRaises(Exception):
            parse_and_validate_query(bad)


class ChatServiceUnderstandTests(TestCase):
    def test_returns_location_when_resolvable(self):
        service = ChatService(llm=FakeLLM(dict(VALID_QUERY)))
        with patch("chatbot.services.location_service.search", return_value=[
            {"name": "Jaipur", "country": "India", "latitude": 26.9124, "longitude": 75.7873}
        ]), patch("chatbot.services.weather_service.current", return_value={
            "location": {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873},
            "current": {"temperature_c": 31.2},
        }), patch("chatbot.services.weather_service.forecast", return_value={
            "daily": [{"date": "2026-09-06", "temperature_max_c": 34.5}]
        }):
            result = service.understand("Will it rain tomorrow in Jaipur?")
        self.assertEqual(result["intent"], "forecast")
        self.assertEqual(result["location"]["name"], "Jaipur")
        self.assertEqual(result["current"]["temperature_c"], 31.2)
        self.assertEqual(result["daily"][0]["date"], "2026-09-06")

    def test_missing_location_returns_none_location(self):
        service = ChatService(llm=FakeLLM(dict(VALID_QUERY, location_name="")))
        with patch("chatbot.services.location_service.search") as search:
            result = service.understand("Will it rain tomorrow?")
        search.assert_not_called()
        self.assertIsNone(result["location"])
        self.assertIsNone(result["current"])
        self.assertIsNone(result["daily"])


class ChatEndpointTests(TestCase):
    def test_health_reveals_model_config(self):
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.get("/api/chat/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_understand_endpoint_returns_grounded_query(self):
        from rest_framework.test import APIClient
        client = APIClient()
        with patch("chatbot.views.chat_service.understand", return_value={
            "intent": "forecast", "location": None
        }) as understand:
            response = client.post(
                "/api/chat/understand/", {"message": "Will it rain tomorrow in Jaipur?"}, format="json"
            )
        understand.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["intent"], "forecast")

    def test_missing_message_returns_400(self):
        from rest_framework.test import APIClient
        response = APIClient().post("/api/chat/understand/", {}, format="json")
        self.assertEqual(response.status_code, 400)


class NoHallucinationGuardTests(TestCase):
    def test_schema_rejects_missing_facts(self):
        """LLM output that omits required keys must fail validation (guard)."""
        missing_intent = dict(VALID_QUERY)
        del missing_intent["intent"]
        with self.assertRaises(Exception):
            parse_and_validate_query(missing_intent)

    def test_schema_rejects_non_dict_lists(self):
        with self.assertRaises(Exception):
            parse_and_validate_query([1, 2, 3])
class VerticalSliceTests(TestCase):
    """The blueprint's core flow (implementation.md section 19)."""

    def _make_service(self, fake_llm):
        return ChatService(
            llm=fake_llm,
            rate_limiter=SlidingWindowRateLimiter(max_requests=100),
        )

    def test_process_message_returns_grounded_answer_and_context(self):
        fake = FakeLLM()
        service = self._make_service(fake)
        with patch("chatbot.services.location_service.search", return_value=[
            {"name": "Jaipur", "country": "India", "latitude": 26.9124, "longitude": 75.7873}
        ]), patch("chatbot.services.weather_service.current", return_value={
            "location": {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873},
            "current": {
                "temperature_c": 31.2,
                "feels_like_c": 34.0,
                "humidity_pct": 61,
                "wind_kmh": 14.2,
                "precipitation_mm": 0.0,
                "condition": "Partly cloudy",
            },
        }), patch("chatbot.services.weather_service.forecast", return_value={
            "daily": [{
                "date": "2026-09-06",
                "temperature_max_c": 34.5,
                "temperature_min_c": 26.1,
                "precipitation_probability_pct": 65,
                "precipitation_mm": 4.2,
                "condition": "Rain showers",
            }]
        }):
            result = service.process_message("Will it rain tomorrow in Jaipur?", client_ip="127.0.0.1")

        self.assertFalse(result["needs_location"])
        self.assertEqual(result["location"]["name"], "Jaipur")
        self.assertEqual(result["weather_context"]["current"]["temperature_c"], 31.2)
        self.assertEqual(result["weather_context"]["forecast_daily"][0]["condition"], "Rain showers")
        self.assertIn("WEATHER_CONTEXT", fake.generated_prompts[0])
        self.assertIn("QUESTION: Will it rain tomorrow in Jaipur?", fake.generated_prompts[0])

    def test_process_message_asks_location_when_missing(self):
        fake = FakeLLM(understand_output=dict(VALID_QUERY, location_name=""))
        service = self._make_service(fake)
        with patch("chatbot.services.location_service.search") as search:
            result = service.process_message("Will it rain tomorrow?", client_ip="127.0.0.1")
        search.assert_not_called()
        self.assertTrue(result["needs_location"])
        self.assertIsNone(result["location"])
        self.assertEqual(result["answer"], fake.generate_output)

    def test_process_message_rate_limit_blocks(self):
        from common.errors import RateLimitedError
        service = ChatService(
            llm=FakeLLM(),
            rate_limiter=SlidingWindowRateLimiter(max_requests=1),
        )
        with patch("chatbot.services.location_service.search", return_value=[
            {"name": "Jaipur", "country": "India", "latitude": 26.9124, "longitude": 75.7873}
        ]), patch("chatbot.services.weather_service.current", return_value={
            "location": {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873},
            "current": {
                "temperature_c": 31.2,
                "feels_like_c": 34.0,
                "humidity_pct": 61,
                "wind_kmh": 14.2,
                "precipitation_mm": 0.0,
                "condition": "Partly cloudy",
            },
        }), patch("chatbot.services.weather_service.forecast", return_value={
            "daily": [{
                "date": "2026-09-06",
                "temperature_max_c": 34.5,
                "temperature_min_c": 26.1,
                "precipitation_probability_pct": 65,
                "precipitation_mm": 4.2,
                "condition": "Rain showers",
            }]
        }):
            service.process_message("first", client_ip="ip")  # uses the single allowed request
            with self.assertRaises(RateLimitedError):
                service.process_message("second", client_ip="ip")

    def test_process_message_comparison_intent_returns_both_cities(self):
        fake = FakeLLM(understand_output=dict(VALID_QUERY, intent="comparison",
                                              secondary_location_name="Delhi"))
        service = self._make_service(fake)
        comparison_entries = [
            {"location": {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873},
             "current": {"temperature_c": 31.2, "feels_like_c": 34.0, "humidity_pct": 61,
                         "wind_kmh": 14.2, "precipitation_mm": 0.0, "condition": "Partly cloudy"}},
            {"location": {"name": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
             "current": {"temperature_c": 34.1, "feels_like_c": 37.0, "humidity_pct": 50,
                         "wind_kmh": 11.0, "precipitation_mm": 0.0, "condition": "Sunny"}},
        ]

        def _fake_search(query, count=1):
            return [{"name": query, "country": "India",
                     "latitude": 26.9124 if query == "Jaipur" else 28.6139,
                     "longitude": 75.7873 if query == "Jaipur" else 77.2090}]

        with patch("chatbot.services.location_service.search", side_effect=_fake_search), \
             patch("chatbot.services.weather_service.current", side_effect=comparison_entries):
            result = service.process_message(
                "Is Delhi hotter than Jaipur right now?", client_ip="127.0.0.1")

        self.assertEqual(result["intent"], "comparison")
        self.assertEqual(result["location"]["name"], "Jaipur")
        self.assertEqual(len(result["weather_context"]["comparison"]), 2)
        self.assertEqual(
            result["weather_context"]["comparison"][1]["current"]["temperature_c"], 34.1)
        self.assertIn("Comparison:", fake.generated_prompts[0])

    def test_process_message_advisory_injects_prototype_alerts(self):
        class FakeAlertsEngine:
            def evaluate_forecast(self, latitude, longitude, location_name, forecast_daily):
                return [{"id": 1, "alert_type": "rain", "severity": "medium",
                         "title": "Heavy rain likely on 2026-09-06",
                         "description": "4.2 mm rain expected (65% probability).",
                         "advice": "Carry rain protection."}]

        fake = FakeLLM(understand_output=dict(VALID_QUERY, intent="advisory", date_reference=""))
        service = ChatService(llm=fake, alerts_engine=FakeAlertsEngine(),
                              rate_limiter=SlidingWindowRateLimiter(max_requests=100))
        with patch("chatbot.services.location_service.search", return_value=[
            {"name": "Jaipur", "country": "India", "latitude": 26.9124, "longitude": 75.7873}
        ]), patch("chatbot.services.weather_service.current", return_value={
            "current": {"temperature_c": 31.2, "feels_like_c": 34.0, "humidity_pct": 61,
                        "wind_kmh": 14.2, "precipitation_mm": 0.0, "condition": "Partly cloudy"}
        }), patch("chatbot.services.weather_service.forecast", return_value={
            "daily": [FULL_DAY]
        }):
            result = service.process_message(
                "Should I carry an umbrella in Jaipur?", client_ip="127.0.0.1")

        self.assertEqual(result["intent"], "advisory")
        self.assertEqual(result["weather_context"]["alerts"][0]["alert_type"], "rain")
        prompt = fake.generated_prompts[0]
        self.assertIn("Heavy rain likely on 2026-09-06", prompt)
        self.assertIn("Give practical advice", prompt)

    def test_process_message_fetches_hourly_for_tonight(self):
        fake = FakeLLM(understand_output=dict(VALID_QUERY, date_reference="tonight"))
        service = self._make_service(fake)
        hourly = [{"time": "2026-09-06T20:00", "temperature_c": 28.9,
                   "precipitation_probability_pct": 70, "precipitation_mm": 2.0,
                   "wind_kmh": 9.0, "condition": "Rain showers"}]
        with patch("chatbot.services.location_service.search", return_value=[
            {"name": "Jaipur", "country": "India", "latitude": 26.9124, "longitude": 75.7873}
        ]), patch("chatbot.services.weather_service.current", return_value={
            "current": {"temperature_c": 31.2, "feels_like_c": 34.0, "humidity_pct": 61,
                        "wind_kmh": 14.2, "precipitation_mm": 0.0, "condition": "Partly cloudy"}
        }), patch("chatbot.services.weather_service.forecast", return_value={
            "daily": [FULL_DAY]
        }), patch("chatbot.services.weather_service.hourly", return_value={
            "hourly": hourly
        }) as hourly_call:
            result = service.process_message(
                "Is it going to rain tonight in Jaipur?", client_ip="127.0.0.1")

        hourly_call.assert_called_once()
        self.assertEqual(result["weather_context"]["hourly"][0]["time"], "2026-09-06T20:00")
        self.assertIn("Hourly (next 1)", fake.generated_prompts[0])

    def test_process_message_imperial_units_pass_through(self):
        fake = FakeLLM(understand_output=dict(VALID_QUERY, units="imperial"))
        service = self._make_service(fake)
        with patch("chatbot.services.location_service.search", return_value=[
            {"name": "Jaipur", "country": "India", "latitude": 26.9124, "longitude": 75.7873}
        ]), patch("chatbot.services.weather_service.current", return_value={
            "current": {"temperature_c": 31.2, "feels_like_c": 34.0, "humidity_pct": 61,
                        "wind_kmh": 14.2, "precipitation_mm": 0.0, "condition": "Partly cloudy"}
        }), patch("chatbot.services.weather_service.forecast", return_value={
            "daily": [FULL_DAY]
        }):
            result = service.process_message(
                "What is the weather in Jaipur tomorrow in Fahrenheit?", client_ip="127.0.0.1")

        self.assertEqual(result["weather_context"]["units"], "imperial")
        self.assertIn("Units: imperial", fake.generated_prompts[0])

    def test_process_message_hindi_prompt_and_language(self):
        fake = FakeLLM(understand_output=dict(VALID_QUERY, language="hi"))
        service = self._make_service(fake)
        with patch("chatbot.services.location_service.search", return_value=[
            {"name": "Jaipur", "country": "India", "latitude": 26.9124, "longitude": 75.7873}
        ]), patch("chatbot.services.weather_service.current", return_value={
            "current": {"temperature_c": 31.2, "feels_like_c": 34.0, "humidity_pct": 61,
                        "wind_kmh": 14.2, "precipitation_mm": 0.0, "condition": "Partly cloudy"}
        }), patch("chatbot.services.weather_service.forecast", return_value={
            "daily": [FULL_DAY]
        }):
            result = service.process_message(
                "क्या कल जयपुर में बारिश होगी?", client_ip="127.0.0.1")

        self.assertEqual(result["language"], "hi")
        self.assertIn("Hindi (Devanagari script)", fake.generated_prompts[0])


class ChatEndpointFullTests(TestCase):
    def test_chat_endpoint_runs_full_flow(self):
        from rest_framework.test import APIClient
        client = APIClient()
        with patch("chatbot.views.chat_service.process_message", return_value={
            "answer": "It will rain in Jaipur tomorrow.",
            "needs_location": False,
        }) as process:
            response = client.post(
                "/api/chat/", {"message": "Will it rain tomorrow in Jaipur?"}, format="json"
            )
        process.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "It will rain in Jaipur tomorrow.")

    def test_chat_endpoint_missing_message_400(self):
        from rest_framework.test import APIClient
        response = APIClient().post("/api/chat/", {}, format="json")
        self.assertEqual(response.status_code, 400)
