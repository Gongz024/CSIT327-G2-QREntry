from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    # IMPORTANT: All other paths (login, logout, home) are REMOVED to focus on registration only.
]