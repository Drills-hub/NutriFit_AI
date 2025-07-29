from allauth.account.adapter import DefaultAccountAdapter


# 유저생성 시 호환성을 위한 adapter
class NutriFitAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        if not hasattr(form, "_has_phone_field"):
            setattr(form, "_has_phone_field", False)

        return super().save_user(request, user, form, commit)
