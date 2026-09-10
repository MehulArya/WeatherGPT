from rest_framework import serializers

from chatbot.models import Conversation, Message


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=1000)
    conversation_id = serializers.IntegerField(
        min_value=1, required=False, allow_null=True
    )
    units = serializers.ChoiceField(
        choices=("metric", "imperial"), default="metric", required=False
    )


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "metadata", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at"]


class ConversationDetailSerializer(ConversationSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ["messages"]