from django.urls import path

from chatbot.views import ChatHealthView, ChatUnderstandView, ChatView

urlpatterns = [
    path('health/', ChatHealthView.as_view()),
    path('understand/', ChatUnderstandView.as_view()),
    path('', ChatView.as_view()),
]