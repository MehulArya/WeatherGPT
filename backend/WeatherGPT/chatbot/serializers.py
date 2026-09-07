"""Generic serializers for the chat API."""

from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=1000)