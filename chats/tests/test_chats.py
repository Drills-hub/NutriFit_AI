from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from accounts.models import User
from chats.models import ChatRoom


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
