from rest_framework import generics
from rest_framework.response import Response

from chatbot.serializers import ChatRequestSerializer
from chatbot.services import chat_service


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
        return Response(chat_service.understand(**serializer.validated_data))


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
