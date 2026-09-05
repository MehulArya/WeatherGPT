from django.urls import path

from locations.views import LocationSearchView

urlpatterns = [
    path('', LocationSearchView.as_view()),
]