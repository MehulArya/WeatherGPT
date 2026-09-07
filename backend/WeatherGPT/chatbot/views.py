from rest_framework import generics
from rest_framework.response import Response

from chatbot.serializers import ChatRequestSerializer
from chatbot.services import chat_service


class ChatHealthView(generics.GenericAPIView):
    """Config probe - returns provider/model from env (no API call)."""

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
