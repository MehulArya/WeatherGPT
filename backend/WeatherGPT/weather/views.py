"""Thin generic API views for current weather, forecast, hourly, and comparison.

Business logic lives in `weather.services.WeatherService`.
"""
from rest_framework import generics
from rest_framework.response import Response

from weather.serializers import (
    CompareQuerySerializer,
    CoordinatesSerializer,
    ForecastQuerySerializer,
    HourlyQuerySerializer,
)
from weather.services import weather_service


class CurrentWeatherView(generics.GenericAPIView):
    serializer_class = CoordinatesSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(weather_service.current(**serializer.validated_data))


class ForecastView(generics.GenericAPIView):
    serializer_class = ForecastQuerySerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(weather_service.forecast(**serializer.validated_data))


class HourlyForecastView(generics.GenericAPIView):
    serializer_class = HourlyQuerySerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(weather_service.hourly(**serializer.validated_data))


class CityCompareView(generics.GenericAPIView):
    serializer_class = CompareQuerySerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(weather_service.compare(**serializer.validated_data))
