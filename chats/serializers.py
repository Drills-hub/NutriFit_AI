from rest_framework import serializers
from .models import ChatRoom


# 채팅방 serializer
class ChatRoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatRoom
        fields = ["id", "user", "title", "created_at", "updated_at"]
        read_only_fields = ("user",)
