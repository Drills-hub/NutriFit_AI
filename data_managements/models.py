import uuid
from django.db import models
from accounts.models import User


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


# 제조사
class Manufacturer(DataBaseModel):

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "manufacturer"
        verbose_name = "제조사"
        verbose_name_plural = "제조사 목록"
        ordering = ["name"]

    def __str__(self):
        return self.name


# 건강기능식품 원료 정보
class Ingredient(DataBaseModel):
    name = models.CharField(max_length=255, unique=True, help_text="품목명")
    functionality = models.TextField(help_text="기능성")
    precautions = models.TextField(blank=True, null=True, help_text="섭취 시 주의사항")
    daily_intake_low = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="일일섭취량 하한",
    )
    daily_intake_high = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="일일섭취량 상한",
    )
    unit = models.CharField(max_length=50, blank=True, help_text="일일섭취량 단위")
    remark = models.TextField(blank=True, help_text="비고")
    registration_date = models.DateField(null=True, blank=True, help_text="최초 등록일")
    last_modified_date = models.DateField(
        null=True, blank=True, help_text="최종 수정일"
    )

    class Meta:
        db_table = "ingredient"
        verbose_name = "원료"
        verbose_name_plural = "원료 목록"
        ordering = ["name"]

    def __str__(self):
        return self.name


# 건강기능식품 제품 정보
class DietarySupplements(DataBaseModel):
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        related_name="products",
        help_text="제품을 제조한 업체명",
    )
    report_number = models.CharField(
        max_length=255, unique=True, help_text="인증번호 (제품 고유 식별자)"
    )
    name = models.CharField(max_length=255, help_text="제품명")
    registration_date = models.DateField(null=True, blank=True, help_text="등록일자")
    appearance = models.TextField(blank=True, help_text="성상")
    usage_instructions = models.TextField(blank=True, help_text="용도 및 용법")
    serving_size = models.CharField(max_length=100, blank=True, help_text="섭취량")
    serving_method = models.TextField(blank=True, help_text="섭취 방법")
    shelf_life = models.CharField(max_length=255, blank=True, help_text="유통기한")
    storage_method = models.TextField(blank=True, help_text="보존방법")
    precautions = models.TextField(blank=True, help_text="섭취시 주의사항")
    main_functionality = models.TextField(blank=True, help_text="주요 기능성")
    standards_and_specifications = models.TextField(
        blank=True, help_text="기준 및 규격"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="DietarySupplementsIngredient",
        related_name="products",
        help_text="제품에 포함된 원료 목록 (M:N)",
    )

    class Meta:
        db_table = "dietary_supplements"
        verbose_name = "건강기능식품"
        verbose_name_plural = "건강기능식품 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


# 건강기능식품과 원료의관계
class DietarySupplementsIngredient(DataBaseModel):
    dietary_supplements = models.ForeignKey(
        DietarySupplements, on_delete=models.CASCADE, help_text="제품 (FK)"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, help_text="원료 (FK)"
    )
    content = models.DecimalField(
        max_digits=20, decimal_places=2, help_text="원료 함량"
    )

    class Meta:
        db_table = "dietary_supplements_ingredient"
        verbose_name = "건강기능식품-원료 관계"
        verbose_name_plural = "건강기능식품-원료 관계 목록"
        unique_together = ("dietary_supplements", "ingredient")
        ordering = ["dietary_supplements__name", "ingredient__name"]

    def __str__(self):
        return f"{self.dietary_supplements.name} - {self.ingredient.name}"


# 사용자의 영양제 섭취 정보
class UserSupplementIntake(DataBaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="사용자 (FK)")
    supplement = models.ForeignKey(
        DietarySupplements, on_delete=models.CASCADE, help_text="섭취 중인 영양제 (FK)"
    )

    intake_amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="섭취량"
    )

    class Meta:
        db_table = "user_supplement_intake"
        verbose_name = "사용자 섭취 영양제"
        verbose_name_plural = "사용자 섭취 영양제 목록"
        unique_together = ("user", "supplement")

    def __str__(self):
        return f"{self.user.username} - {self.supplement.name}"
