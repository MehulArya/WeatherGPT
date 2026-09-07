from django.urls import path

from chatbot.views import ConversationDetailView, ConversationListView

urlpatterns = [
    path('', ConversationListView.as_view()),
    path('<int:pk>/', ConversationDetailView.as_view()),
]