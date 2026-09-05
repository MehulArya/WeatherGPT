"Thin generic API view for location search."
from rest_framework import generics
from rest_framework.response import Response

from locations.serializers import LocationQuerySerializer
from locations.services import location_service


class LocationSearchView(generics.GenericAPIView):
    serializer_class = LocationQuerySerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response({"results": location_service.search(**serializer.validated_data)})
