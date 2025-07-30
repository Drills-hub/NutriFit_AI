from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Allergy, ChronicDisease, Medication, User


# 지병, 알레르기, 복용 약물 모델을 위한 기본 Admin 클래스
class HealthInfoBaseAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("개인 정보", {"fields": ("nickname", "birth_date", "gender")}),
        (
            "건강 정보",
            {
                "fields": (
                    "health_goals",
                    "chronic_diseases",
                    "allergies",
                    "medications",
                )
            },
        ),
        (
            "권한",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("주요 날짜", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("email", "nickname", "is_staff")
    search_fields = ("email", "nickname")
    ordering = ("email",)
    filter_horizontal = (
        "groups",
        "user_permissions",
        "chronic_diseases",
        "allergies",
        "medications",
    )


@admin.register(ChronicDisease)
class ChronicDiseaseAdmin(HealthInfoBaseAdmin):
    pass


@admin.register(Allergy)
class AllergyAdmin(HealthInfoBaseAdmin):
    pass


@admin.register(Medication)
class MedicationAdmin(HealthInfoBaseAdmin):
    pass
