from core.models import DataBaseModel
from accounts.models import User
from django.db import models


# 채팅방 모델
class ChatRoom(DataBaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_rooms", verbose_name="사용자"
    )
    title = models.CharField(max_length=255, blank=True, verbose_name="대화방 제목")

    class Meta:
        verbose_name = "대화방"
        verbose_name_plural = "대화방 목록"
        ordering = ["-updated_at"]

    def __str__(self):
        # user.nickname이 없을 경우를 대비하여 user.email 사용
        user_identifier = getattr(self.user, "nickname", self.user.email)
        return f"{user_identifier}님의 대화방 ({str(self.id)[:8]})"


# 채팅 메세지 모델
class Message(DataBaseModel):
    class SenderType(models.TextChoices):
        USER = "user", "사용자"
        AI = "ai", "AI"

    class MessageType(models.TextChoices):
        TEXT = "text", "텍스트"
        SYSTEM = "system", "시스템"

    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="대화방",
    )
    sender = models.CharField(
        max_length=10, choices=SenderType.choices, verbose_name="사용자"
    )
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        verbose_name="메시지 유형",
    )
    content = models.TextField(verbose_name="메시지 내용")

    class Meta:
        verbose_name = "메시지"
        verbose_name_plural = "메시지 목록"
        ordering = ["created_at"]

    def __str__(self):
        if self.sender == self.SenderType.USER:

            user_identifier = getattr(self.chat_room.user, "nickname")
            return f"[{user_identifier}] {self.content[:30]}"
        return f"[{self.get_sender_display()}] {self.content[:30]}"
