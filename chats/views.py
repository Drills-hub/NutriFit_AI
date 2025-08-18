from rest_framework import viewsets, permissions, filters
from rest_framework.pagination import CursorPagination
from .models import ChatRoom
from .serializers import ChatRoomSerializer


# 채팅방 cursor pagination
class ChatRoomCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-updated_at"


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
