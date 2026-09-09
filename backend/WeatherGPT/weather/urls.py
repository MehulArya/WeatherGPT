from django.urls import path

from weather.views import CityCompareView, CurrentWeatherView, ForecastView, HourlyForecastView

urlpatterns = [
    path('current/', CurrentWeatherView.as_view()),
    path('forecast/', ForecastView.as_view()),
    path('hourly/', HourlyForecastView.as_view()),
    path('compare/', CityCompareView.as_view()),
]