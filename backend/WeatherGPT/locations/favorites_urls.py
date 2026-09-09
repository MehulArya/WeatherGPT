from django.urls import path

from locations.views import SavedLocationDeleteView, SavedLocationListCreateView

urlpatterns = [
    path("", SavedLocationListCreateView.as_view(), name="saved-location-list"),
    path("<int:pk>/", SavedLocationDeleteView.as_view(), name="saved-location-detail"),
]