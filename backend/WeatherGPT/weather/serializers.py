from rest_framework import serializers


class CoordinatesSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)


class ForecastQuerySerializer(CoordinatesSerializer):
    days = serializers.IntegerField(min_value=1, max_value=16, default=7)


class HourlyQuerySerializer(CoordinatesSerializer):
    hours = serializers.IntegerField(min_value=1, max_value=48, default=24)


class CompareQuerySerializer(serializers.Serializer):
    city1 = serializers.CharField(min_length=1, max_length=100)
    city2 = serializers.CharField(min_length=1, max_length=100)