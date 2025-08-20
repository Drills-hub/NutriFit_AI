from rest_framework import serializers
from .models import ChatRoom, Message


# 채팅방 serializer
class ChatRoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatRoom
        fields = ["id", "user", "title", "created_at", "updated_at"]
        read_only_fields = ("user",)


# 메시지 serializer
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "chat_room",
            "sender",
            "message_type",
            "content",
            "created_at",
        ]
        read_only_fields = (
            "chat_room",
            "sender",
            "message_type",
            "created_at",
        )
