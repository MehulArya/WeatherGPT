"""OpenAI-compatible LLM provider over HTTP.

Reads LLM_API_KEY / LLM_MODEL / LLM_BASE_URL from the environment (.env).
Kept behind the LLMService interface so providers can be swapped.
"""
import httpx
import logging
import os
from typing import Any, Dict, List

from chatbot.llm.base import LLMService
from common.errors import LlmError

logger = logging.getLogger(__name__)

QUERY_UNDERSTANDING_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["current_weather", "forecast", "comparison", "advisory", "alert"]},
        "location_name": {"type": "string"},
        "secondary_location_name": {"type": "string"},
        "date_reference": {"type": "string"},
        "language": {"type": "string", "enum": ["en", "hi"]},
        "units": {"type": "string", "enum": ["metric", "imperial"]},
        "weather_parameters": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["intent", "location_name", "date_reference", "language", "weather_parameters"],
    "additionalProperties": False,
}

HTTP_TIMEOUT_SECONDS = 30.0


class OpenAICompatibleLLM(LLMService):
    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
        timeout: float = HTTP_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport = None,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY") or ""
        self.model = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        self.base_url = (base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def _chat(self, messages: List[Dict[str, str]], json_mode: bool = False) -> Dict[str, Any]:
        if not self.api_key:
            raise LlmError()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            response = self._client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("LLM request to %s failed", self.base_url)
            raise LlmError() from exc

    def understand_query(self, user_message: str) -> Dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict query parser. Extract a structured weather query "
                    "from the user message. Reply with JSON only, matching this schema: "
                    f"{QUERY_UNDERSTANDING_SCHEMA}. "
                    "Set weather_parameters to an array like temperature/precipitation/wind. "
                    "If no location is mentioned, set location_name to an empty string. "
                    "If the user compares two places (X vs Y, X or Y, hotter/colder/warmer, "
                    "which is better), set intent to 'comparison', put the first place in "
                    "location_name and the second in secondary_location_name. "
                    "Otherwise leave secondary_location_name as an empty string. "
                    "If the message mentions fahrenheit, °F, imperial, or mph, set units "
                    "to 'imperial'; otherwise set units to 'metric'. "
                    "If the message is written in Hindi (Devanagari script) or Hinglish "
                    "asking about the weather, set language to 'hi'; otherwise 'en'."
                ),
            },
            {"role": "user", "content": user_message},
        ]
        data = self._chat(messages, json_mode=True)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.exception("Unexpected LLM response shape: %.400s", data)
            raise LlmError() from exc

    def generate(
        self,
        system_prompt: str,
        user_content: str,
        json_mode: bool = False,
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        data = self._chat(messages, json_mode=json_mode)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.exception("Unexpected LLM response shape: %.400s", data)
            raise LlmError() from exc


# Singleton consumed by the chat service
llm_service = OpenAICompatibleLLM()