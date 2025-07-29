from django.urls import path, include
from .views import UserDeleteView

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("signup/", include("dj_rest_auth.registration.urls")),
    path("user/delete/", UserDeleteView.as_view(), name="account_delete"),
]
