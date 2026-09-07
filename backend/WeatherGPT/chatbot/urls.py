from django.urls import path

from chatbot.views import ChatHealthView, ChatUnderstandView

urlpatterns = [
    path('health/', ChatHealthView.as_view()),
    path('understand/', ChatUnderstandView.as_view()),
]