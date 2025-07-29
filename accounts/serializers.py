from allauth.account.forms import SignupForm
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from django.db import transaction

from .models import User, ChronicDisease, Allergy, Medication


class SignUpSerializer(RegisterSerializer):
    username = None
    nickname = serializers.CharField(max_length=30)
    birth_date = serializers.DateField(required=False)
    gender = serializers.CharField(max_length=10, required=False)
    health_goals = serializers.CharField(max_length=255, required=False)
    chronic_diseases = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ChronicDisease.objects.all(), required=False
    )
    allergies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Allergy.objects.all(), required=False
    )
    medications = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Medication.objects.all(), required=False
    )

    def validate_nickname(self, value):
        if User.objects.filter(nickname__iexact=value).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")
        return value

    def get_cleaned_data(self):
        data = {
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
            "password2": self.validated_data.get("password2", ""),
        }
        return data

    @transaction.atomic
    def save(self, request):
        form = SignupForm(self.get_cleaned_data())
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)

        user = form.save(request)

        user.nickname = self.validated_data.get("nickname", "")
        user.birth_date = self.validated_data.get("birth_date")
        user.gender = self.validated_data.get("gender")
        user.health_goals = self.validated_data.get("health_goals")
        user.save()

        chronic_diseases_data = self.validated_data.get("chronic_diseases", [])
        if chronic_diseases_data:
            user.chronic_diseases.set(chronic_diseases_data)

        allergies_data = self.validated_data.get("allergies", [])
        if allergies_data:
            user.allergies.set(allergies_data)

        medications_data = self.validated_data.get("medications", [])
        if medications_data:
            user.medications.set(medications_data)

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "nickname",
            "birth_date",
            "gender",
            "health_goals",
            "chronic_diseases",
            "allergies",
            "medications",
        )
        read_only_fields = ("email",)
