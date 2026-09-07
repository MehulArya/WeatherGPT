from django.urls import path

from . import views

urlpatterns = [
    path("", views.AlertListCreateView.as_view(), name="alert-list"),
]