from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField("이메일", unique=True)
    nickname = models.CharField("닉네임", max_length=30, unique=True)
    birth_date = models.DateField("생년월일", null=True, blank=True)
    gender = models.CharField(
        "성별",
        max_length=10,
        choices=[("M", "남"), ("F", "여"), ("O", "기타")],
        null=True,
        blank=True,
    )
    health_goals = models.CharField("건강 목표", max_length=255, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"

    def __str__(self):
        return self.email
