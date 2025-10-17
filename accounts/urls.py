from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("home/", views.home_view, name="home"),
     path('event/<int:event_id>/', views.event_detail_view, name='event_detail'),
    path("logout/", views.logout_view, name="logout"),
    path("confirm_logout/", views.confirm_logout_view, name="confirm_logout"),
    path("organizer/", views.organizer_view, name="organizer"),

    path('organizer/create-event/', views.create_event_view, name='create_event'),
    path('event-created/', views.event_created_view, name='event_created'),
    path('event/', views.view_events_view, name='event'),
    path('event/<int:event_id>/edit/', views.edit_event_view, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event_view, name='delete_event'),

    # Forgot Password
    path(
        "password_reset/",
    auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.html",
        subject_template_name="accounts/password_reset_subject.txt",
        extra_email_context={"brand_name": "Event CIT"},
        from_email="Event CIT <noreply.eventcit@gmail.com>",  # Optional custom sender name
        success_url="/accounts/password_reset_done/",
    ),
    name="password_reset",
),
    path(
        "password_reset_done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
