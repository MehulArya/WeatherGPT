from django.urls import path

from locations.views import LocationSearchView, ReverseGeocodeView

urlpatterns = [
    path('', LocationSearchView.as_view()),
    path('reverse/', ReverseGeocodeView.as_view()),
]