from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/weather/location/', include('locations.urls')),
    path('api/weather/', include('weather.urls')),
    path('api/chat/', include('chatbot.urls')),
    path('api/conversations/', include('chatbot.conversations_urls')),
    path('api/alerts/', include('alerts.urls')),
]
