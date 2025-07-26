from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class HealthInfoBase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("이름", max_length=100, unique=True)
    description = models.TextField("설명", blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ChronicDisease(HealthInfoBase):
    class Meta:
        verbose_name = "지병"
        verbose_name_plural = "지병 목록"


class Allergy(HealthInfoBase):
    class Meta:
        verbose_name = "알레르기"
        verbose_name_plural = "알레르기 목록"


class Medication(HealthInfoBase):
    class Meta:
        verbose_name = "복용 약물"
        verbose_name_plural = "복용 약물 목록"


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
    chronic_diseases = models.ManyToManyField(
        ChronicDisease, blank=True, verbose_name="지병"
    )
    allergies = models.ManyToManyField(Allergy, blank=True, verbose_name="알레르기")
    medications = models.ManyToManyField(
        Medication, blank=True, verbose_name="복용 약물"
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname"]

    class Meta:
        verbose_name = "사용자"
        verbose_name_plural = "사용자 목록"

    def __str__(self):
        return self.email
