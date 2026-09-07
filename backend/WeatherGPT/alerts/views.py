from django.utils import timezone
from rest_framework import generics

from .models import Alert
from .serializers import AlertQuerySerializer, AlertSerializer
from .services import AlertEngine


class AlertListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/alerts/

    GET lists active alerts; when latitude/longitude query params are given
    the prototype rule engine evaluates the current forecast for that
    location first. POST creates an alert row directly (useful for demos).
    """

    queryset = Alert.objects.all()
    serializer_class = AlertSerializer

    def get_queryset(self):
        params = AlertQuerySerializer(data=self.request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data
        if data.get("latitude") is not None:
            AlertEngine().evaluate_and_save(
                latitude=data["latitude"],
                longitude=data["longitude"],
                location_name=data.get("location_name", ""),
                days=data.get("days", 7),
            )
        return super().get_queryset().filter(ends_at__gte=timezone.now())