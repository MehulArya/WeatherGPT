from django.urls import path

from weather.views import CurrentWeatherView, ForecastView

urlpatterns = [
    path('current/', CurrentWeatherView.as_view()),
    path('forecast/', ForecastView.as_view()),
]