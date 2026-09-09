"""Generic serializers for location search, reverse geocoding, and favorites."""

from rest_framework import serializers

from locations.models import SavedLocation


class LocationQuerySerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1, max_length=100)
    count = serializers.IntegerField(min_value=1, max_value=10, default=5)


class ReverseGeocodeQuerySerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)


class SavedLocationSerializer(serializers.ModelSerializer):
    client_key = serializers.CharField(min_length=8, max_length=64)

    class Meta:
        model = SavedLocation
        fields = ["id", "client_key", "name", "country", "latitude", "longitude", "created_at"]
        read_only_fields = ("id", "created_at")