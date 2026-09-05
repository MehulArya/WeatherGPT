"""URL configuration for WeatherGPT project.

All API endpoints live under the /api/ prefix.
Each functional app owns its own URL module (thin HTTP layer).
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/weather/', include('weather.urls')),
    path('api/weather/location/', include('locations.urls')),
    path('api/chat/', include('chatbot.urls')),
    path('api/alerts/', include('alerts.urls')),
]
