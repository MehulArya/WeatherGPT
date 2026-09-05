"""Shared API error envelope (implementation.md section 25).

Every API error returns:
    {"error": {"code": "<CODE>", "message": "<human readable>"}}

Views never write try/except blocks - services raise ApiError subclasses
and the custom DRF exception handler converts them to the envelope.
"""
from rest_framework import serializers
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

# Error codes (implementation.md section 25)
ERROR_LOCATION_NOT_FOUND = "LOCATION_NOT_FOUND"
ERROR_WEATHER_PROVIDER = "WEATHER_PROVIDER_ERROR"
ERROR_WEATHER_UNAVAILABLE = "WEATHER_DATA_UNAVAILABLE"
ERROR_LLM = "LLM_ERROR"
ERROR_INVALID_QUERY = "INVALID_QUERY"
ERROR_RATE_LIMITED = "RATE_LIMITED"


class ApiError(Exception):
    """Base error that maps to the shared envelope."""

    status_code = 400

    def __init__(self, code: str, message: str, status_code: int = None):
        self.code = code
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class LocationNotFoundError(ApiError):
    def __init__(self, query: str):
        super().__init__(
            ERROR_LOCATION_NOT_FOUND,
            f"No location found for query: {query}",
            status_code=404,
        )


class WeatherProviderError(ApiError):
    def __init__(self):
        super().__init__(
            ERROR_WEATHER_PROVIDER,
            "Weather provider is unavailable. Please try again later.",
            status_code=503,
        )


class WeatherDataUnavailableError(ApiError):
    def __init__(self):
        super().__init__(
            ERROR_WEATHER_UNAVAILABLE,
            "Weather data is unavailable for this location.",
            status_code=404,
        )


class LlmError(ApiError):
    def __init__(self):
        super().__init__(
            ERROR_LLM,
            "The language model is unavailable. Please try again later.",
            status_code=503,
        )


def build_error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def api_exception_handler(exc, context):
    """Convert ApiError and validation failures into the shared envelope."""
    if isinstance(exc, ApiError):
        return Response(build_error_body(exc.code, exc.message), status=exc.status_code)
    if isinstance(exc, (serializers.ValidationError, drf_exceptions.ValidationError)):
        return Response(
            build_error_body(ERROR_INVALID_QUERY, exc.detail),
            status=400,
        )
    return drf_exception_handler(exc, context)