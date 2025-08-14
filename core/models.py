from django.db import models
import uuid


# 모든 모델이 공통으로 사용할 기본 필드를 정의한 추상 모델
class DataBaseModel(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
