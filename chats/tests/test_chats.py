from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from accounts.models import User
from chats.models import ChatRoom, Message


# chats 앱 API 테스트
class ChatRoomAPITests(APITestCase):

    def setUp(self):
        # 테스트용 사용자 2명 생성
        self.user = User.objects.create_user(
            email="testuser@example.com", password="password123", nickname="testuser"
        )
        self.other_user = User.objects.create_user(
            email="otheruser@example.com", password="password123", nickname="otheruser"
        )
        # self.user로 클라이언트 인증
        self.client.force_authenticate(user=self.user)

        # self.user가 소유한 채팅방 생성
        self.chatroom = ChatRoom.objects.create(user=self.user, title="My Chat Room")
        # self.other_user가 소유한 채팅방 생성
        self.other_chatroom = ChatRoom.objects.create(
            user=self.other_user, title="Other's Chat Room"
        )

    # 채팅방 성공 테스트
    def test_create_chatroom(self):
        print("\n채팅방 생성 성공 테스트\n")
        url = reverse("chatroom-list")
        data = {"title": "New Chat Room"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ChatRoom.objects.count(), 3)
        self.assertEqual(response.data["title"], "New Chat Room")
        self.assertEqual(response.data["user"], self.user.id)

    # 채팅방 목록 조회 성공 테스트
    def test_list_chatrooms(self):
        print("\n채팅방 목록 조회 성공 테스트\n")
        url = reverse("chatroom-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # pagination 적용 시 results 키 확인
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], self.chatroom.title)

    # 채팅방 상세 조회 성공 테스트
    def test_retrieve_chatroom(self):
        print("\n채팅방 상세 조회 성공 테스트\n")
        url = reverse("chatroom-detail", kwargs={"pk": self.chatroom.pk})
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.chatroom.title)

    # 채팅방 정보 수정 성공 테스트
    def test_update_chatroom(self):
        print("\n채팅방 정보 수정 성공 테스트\n")
        url = reverse("chatroom-detail", kwargs={"pk": self.chatroom.pk})
        update_data = {"title": "Updated Chat Room Title"}
        response = self.client.put(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chatroom.refresh_from_db()
        self.assertEqual(self.chatroom.title, "Updated Chat Room Title")

    # 채팅방 삭제 성공 테스트
    def test_delete_chatroom(self):
        print("\n채팅방 삭제 성공 테스트\n")
        url = reverse("chatroom-detail", kwargs={"pk": self.chatroom.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatRoom.objects.filter(pk=self.chatroom.pk).exists())

    # 채팅방 검색 성공 테스트
    def test_search_chatroom(self):
        print("\n채팅방 검색 성공 테스트\n")
        # 검색을 위한 추가 채팅방 생성
        ChatRoom.objects.create(user=self.user, title="Another Searchable Room")
        url = reverse("chatroom-list") + "?search=MY"
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "My Chat Room")

    # 다른 사용자 채팅방 접근 권한 테스트
    def test_chatroom_permission(self):
        print("\n다른 사용자 채팅방 접근 권한 테스트\n")
        url_retrieve = reverse("chatroom-detail", kwargs={"pk": self.other_chatroom.pk})
        response_retrieve = self.client.get(url_retrieve, format="json")
        self.assertEqual(response_retrieve.status_code, status.HTTP_404_NOT_FOUND)

        # 다른 사용자의 채팅방 수정 시도
        url_update = reverse("chatroom-detail", kwargs={"pk": self.other_chatroom.pk})
        update_data = {"title": "Hacked"}
        response_update = self.client.put(url_update, update_data, format="json")
        self.assertEqual(response_update.status_code, status.HTTP_404_NOT_FOUND)

        # 다른 사용자의 채팅방 삭제 시도
        url_delete = reverse("chatroom-detail", kwargs={"pk": self.other_chatroom.pk})
        response_delete = self.client.delete(url_delete)
        self.assertEqual(response_delete.status_code, status.HTTP_404_NOT_FOUND)


class MessageAPITests(APITestCase):

    def setUp(self):
        # 테스트용 사용자 2명 생성
        self.user = User.objects.create_user(
            email="testuser@example.com", password="password123", nickname="testuser"
        )
        self.other_user = User.objects.create_user(
            email="otheruser@example.com", password="password123", nickname="otheruser"
        )
        # self.user로 클라이언트 인증
        self.client.force_authenticate(user=self.user)

        # self.user가 소유한 채팅방 생성
        self.chatroom = ChatRoom.objects.create(user=self.user, title="My Chat Room")
        # self.other_user가 소유한 채팅방 생성
        self.other_chatroom = ChatRoom.objects.create(
            user=self.other_user, title="Other's Chat Room"
        )

    # 메시지 생성 시 AI 응답 자동 생성 테스트
    def test_create_message_creates_ai_response(self):
        print("\n메시지 생성 시 AI 응답 자동 생성 테스트\n")
        url = reverse("chat_message-list", kwargs={"chat_room_pk": self.chatroom.pk})
        data = {"content": "안녕하세요 AI"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 동일 대화방에 사용자/AI 메시지 두 건이 생성
        messages = Message.objects.filter(chat_room=self.chatroom).order_by(
            "created_at"
        )
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].sender, Message.SenderType.USER)
        self.assertEqual(messages[1].sender, Message.SenderType.AI)

        self.assertEqual(response.data["content"], data["content"])
        self.assertEqual(response.data["sender"], Message.SenderType.USER)
        self.assertEqual(response.data["message_type"], Message.MessageType.TEXT)
        self.assertEqual(response.data["chat_room"], self.chatroom.id)

    # 메시지 목록 조회
    def test_list_messages_by_chatroom_with_pagination(self):
        print("\n메시지 목록 조회 성공 테스트\n")
        # 현재 대화방에 메시지 생성 (사용자 + AI 자동 생성)
        url = reverse("chat_message-list", kwargs={"chat_room_pk": self.chatroom.pk})
        self.client.post(url, {"content": "첫 메세지"}, format="json")

        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        results = response.data["results"]
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)

        # 모든 결과가 요청한 chat_room에 속하는지 확인
        self.assertTrue(all(item["chat_room"] == self.chatroom.id for item in results))

    # 메시지 상세 조회 성공 테스트
    def test_retrieve_message_detail(self):
        print("\n메시지 상세 조회 성공 테스트\n")
        url_list = reverse(
            "chat_message-list", kwargs={"chat_room_pk": self.chatroom.pk}
        )
        resp_create = self.client.post(
            url_list, {"content": "메세지 확인"}, format="json"
        )
        self.assertEqual(resp_create.status_code, status.HTTP_201_CREATED)
        message_id = resp_create.data["id"]

        url_detail = reverse(
            "chat_message-detail",
            kwargs={"chat_room_pk": self.chatroom.pk, "pk": message_id},
        )
        resp_detail = self.client.get(url_detail, format="json")
        self.assertEqual(resp_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_detail.data["id"], message_id)
        self.assertEqual(resp_detail.data["content"], "메세지 확인")
        self.assertEqual(resp_detail.data["sender"], Message.SenderType.USER)
        self.assertEqual(resp_detail.data["chat_room"], self.chatroom.id)
