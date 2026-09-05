"""Generic serializer for location search query parameters."""

from rest_framework import serializers


class LocationQuerySerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1, max_length=100)
    count = serializers.IntegerField(min_value=1, max_value=10, default=5)