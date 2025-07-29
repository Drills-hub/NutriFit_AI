from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from accounts.models import User


# 회원가입, 로그인, 로그아웃 등 인증 관련 테스트
class UserAuthTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="login@example.com", password="password123", nickname="loginuser"
        )

    def test_user_signup_success(self):
        print("\n회원가입 성공 테스트\n")
        url = reverse("rest_register")
        signup_data = {
            "email": "test@example.com",
            "password1": "1q2w3e4r!@#",
            "password2": "1q2w3e4r!@#",
            "nickname": "testuser123",
            "health_goals": "눈 건강",
        }
        response = self.client.post(url, signup_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=signup_data["email"]).exists())

    def test_user_login_and_logout(self):
        print("\n로그인 및 로그아웃 성공 테스트\n")
        login_url = reverse("rest_login")
        login_data = {"email": self.user.email, "password": "password123"}
        response = self.client.post(login_url, login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)  # refresh 토큰 확인

        access_token = response.data["access"]
        refresh_token = response.data["refresh"]  # refresh 토큰 저장

        logout_url = reverse("rest_logout")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        # 로그아웃 시 refresh 토큰 전송
        response = self.client.post(
            logout_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# 회원정보 조회, 수정, 탈퇴 등 사용자 관리 관련 테스트
class UserManagementTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="manage@example.com",
            password="password123",
            nickname="manageuser",
        )
        self.client.force_authenticate(user=self.user)

    def test_user_detail_retrieve(self):
        print("\n회원정보 조회 성공 테스트\n")
        url = reverse("rest_user_details")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["nickname"], self.user.nickname)

    def test_user_detail_update(self):
        print("\n회원정보 수정 성공 테스트\n")
        url = reverse("rest_user_details")
        update_data = {"nickname": "updateduser", "health_goals": "Get stronger"}
        response = self.client.put(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, update_data["nickname"])
        self.assertEqual(self.user.health_goals, update_data["health_goals"])

    def test_user_delete(self):
        print("\n회원 탈퇴(비활성화) 성공 테스트\n")
        url = reverse("account_delete")
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
