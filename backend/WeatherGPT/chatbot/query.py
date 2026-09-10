"""Server-side validation of the LLM query-understanding schema.

The LLM output is not trusted until it passes here.
"""
import json

from common.errors import LlmError

VALID_INTENTS = {"current_weather", "forecast", "comparison", "advisory", "alert"}
VALID_LANGUAGES = {"en", "hi"}
VALID_UNITS = {"metric", "imperial"}
VALID_PARAMETERS = {"temperature", "precipitation", "wind", "humidity", "condition"}


def parse_and_validate_query(llm_output) -> dict:
    """Parse LLM structured output and validate against the schema.

    Raises LlmError on any malformed structure. Returns a clean dict.
    """
    if isinstance(llm_output, dict):
        data = llm_output
    elif isinstance(llm_output, str):
        try:
            data = json.loads(llm_output)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LlmError() from exc
    else:
        raise LlmError()

    if not isinstance(data, dict):
        raise LlmError()

    intent = data.get("intent")
    location_name = data.get("location_name")
    secondary_location_name = data.get("secondary_location_name", "")
    date_reference = data.get("date_reference")
    language = data.get("language")
    units = data.get("units", "metric")
    parameters = data.get("weather_parameters")

    if intent not in VALID_INTENTS:
        raise LlmError()
    if not isinstance(location_name, str):
        raise LlmError()
    if not isinstance(secondary_location_name, str):
        raise LlmError()
    if len(secondary_location_name) > 100:
        raise LlmError()
    if not isinstance(date_reference, str):
        raise LlmError()
    if language not in VALID_LANGUAGES:
        raise LlmError()
    if units not in VALID_UNITS:
        raise LlmError()
    if not isinstance(parameters, list) or not parameters:
        raise LlmError()
    if not set(parameters).issubset(VALID_PARAMETERS):
        raise LlmError()

    return {
        "intent": intent,
        "location_name": location_name.strip(),
        "secondary_location_name": secondary_location_name.strip(),
        "date_reference": date_reference.strip(),
        "language": language,
        "units": units,
        "weather_parameters": parameters,
    }