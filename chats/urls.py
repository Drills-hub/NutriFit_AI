from django.urls import path, include

from .views import ChatRoomViewSet, MessageViewSet
from core.routers import NestedRouter

router = NestedRouter()
router.register(r"rooms", ChatRoomViewSet, basename="chatroom")
router.register_nested(
    r"messages",
    MessageViewSet,
    parent_prefix=r"rooms",
    parent_lookup_kwarg="chat_room_pk",
    basename="chat_message",
)

urlpatterns = [
    path("", include(router.urls)),
]
