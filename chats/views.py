from rest_framework import viewsets, permissions, filters
from rest_framework.pagination import CursorPagination
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer


# 채팅방 cursor pagination
class ChatRoomCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-updated_at"


# 메시지 cursor pagination
class MessageCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"


# 채팅방 viewset
class ChatRoomViewSet(viewsets.ModelViewSet):

    queryset = ChatRoom.objects.all().order_by("-updated_at")
    serializer_class = ChatRoomSerializer

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatRoomCursorPagination

    filter_backends = [filters.SearchFilter]
    search_fields = ["title"]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# 메시지 viewset
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessageCursorPagination

    def get_queryset(self):
        chat_room_pk = self.kwargs.get("chat_room_pk")
        return self.queryset.filter(chat_room=chat_room_pk)

    def perform_create(self, serializer):
        chat_room_pk = self.kwargs.get("chat_room_pk")
        chat_room = ChatRoom.objects.get(pk=chat_room_pk)

        # 사용자 메시지 저장
        user_message = serializer.save(
            chat_room=chat_room, sender=Message.SenderType.USER
        )
        # AI 응답 메시지 저장 로직 생성 예정
        Message.objects.create(
            chat_room=chat_room,
            sender=Message.SenderType.AI,
            content=f"AI 응답: 기능 생성 예정",
        )

        chat_room.save()
