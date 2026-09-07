from rest_framework import generics
from rest_framework.response import Response

from chatbot.serializers import (
    ChatRequestSerializer,
    ConversationDetailSerializer,
    ConversationSerializer,
)
from chatbot.services import chat_service
from chatbot.models import Conversation


class ChatHealthView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        from chatbot.llm.provider import llm_service

        return Response(
            {
                "status": "ok",
                "llm_configured": bool(llm_service.api_key),
                "llm_model": llm_service.model,
            }
        )


class ChatUnderstandView(generics.GenericAPIView):
    serializer_class = ChatRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(chat_service.understand(message=serializer.validated_data["message"]))


class ChatView(generics.GenericAPIView):
    """POST /api/chat/ - the full blueprint vertical slice."""

    serializer_class = ChatRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = chat_service.process_message(
            **serializer.validated_data,
            client_ip=request.META.get("REMOTE_ADDR", ""),
        )
        return Response(result)


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    queryset = Conversation.objects.all()


class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationDetailSerializer
    queryset = Conversation.objects.all()
