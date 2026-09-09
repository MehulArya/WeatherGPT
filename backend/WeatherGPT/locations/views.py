"""Thin generic API views for location search, reverse geocoding, and favorites.

Business logic lives in `locations.services`.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from locations.models import SavedLocation
from locations.serializers import (
    LocationQuerySerializer,
    ReverseGeocodeQuerySerializer,
    SavedLocationSerializer,
)
from locations.services import location_service


class LocationSearchView(generics.GenericAPIView):
    serializer_class = LocationQuerySerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response({"results": location_service.search(**serializer.validated_data)})


class ReverseGeocodeView(generics.GenericAPIView):
    """GET with latitude/longitude -> nearest place name (for map clicks)."""

    serializer_class = ReverseGeocodeQuerySerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(location_service.reverse_geocode(**serializer.validated_data))


class SavedLocationListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/favorites/ — bookmarked cities keyed by an anonymous client_key."""

    serializer_class = SavedLocationSerializer

    def get_queryset(self):
        client_key = self.request.query_params.get("client_key", "")
        return SavedLocation.objects.filter(client_key=client_key)


class SavedLocationDeleteView(generics.DestroyAPIView):
    serializer_class = SavedLocationSerializer

    def get_object(self):
        client_key = self.request.query_params.get("client_key") or self.request.data.get(
            "client_key", ""
        )
        return get_object_or_404(SavedLocation, pk=self.kwargs["pk"], client_key=client_key)
