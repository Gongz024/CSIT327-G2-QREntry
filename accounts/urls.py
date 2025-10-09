from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("home/", views.home_view, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("confirm_logout/", views.confirm_logout_view, name="confirm_logout"),
    path("organizer/", views.organizer_view, name="organizer"),
]
