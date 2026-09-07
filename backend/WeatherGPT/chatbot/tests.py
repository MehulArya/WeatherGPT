"""Tests for the chat layer (LLM provider, schema validation, ChatService, endpoints)."""
from unittest.mock import patch

from django.test import TestCase

from chatbot.query import parse_and_validate_query
from chatbot.services import ChatService

VALID_QUERY = {
    "intent": "forecast",
    "location_name": "Jaipur",
    "date_reference": "tomorrow",
    "language": "en",
    "weather_parameters": ["precipitation"],
}


class SchemaValidationTests(TestCase):
    def test_accepts_valid_query(self):
        self.assertEqual(parse_and_validate_query(VALID_QUERY), {
            "intent": "forecast",
            "location_name": "Jaipur",
            "date_reference": "tomorrow",
            "language": "en",
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


class FakeLLM:
    def __init__(self, output):
        self.output = output

    def understand_query(self, message: str):
        return self.output


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
