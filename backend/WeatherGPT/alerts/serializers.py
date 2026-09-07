from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = "__all__"
        read_only_fields = ("id", "source", "is_official", "created_at")


class AlertQuerySerializer(serializers.Serializer):
    """Generic validation for GET /api/alerts/ query parameters."""

    latitude = serializers.DecimalField(
        required=False, max_digits=8, decimal_places=5, min_value=-90, max_value=90
    )
    longitude = serializers.DecimalField(
        required=False, max_digits=9, decimal_places=5, min_value=-180, max_value=180
    )
    days = serializers.IntegerField(required=False, min_value=1, max_value=16, default=7)
    location_name = serializers.CharField(
        required=False, allow_blank=True, max_length=200, default=""
    )

    def validate(self, attrs):
        latitude, longitude = attrs.get("latitude"), attrs.get("longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "Either both latitude and longitude must be provided or both left blank."
            )
        return attrs