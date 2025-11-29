from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("home/", views.home_view, name="home"),
    path('event/<int:event_id>/', views.event_detail_view, name='event_detail'),
    path('event/<int:event_id>/avail-ticket/', views.avail_ticket, name='avail_ticket'),
    path("logout/", views.logout_view, name="logout"),
    path("confirm_logout/", views.confirm_logout_view, name="confirm_logout"),
    path("organizer/", views.organizer_view, name="organizer"),
    path("live-search-tickets/", views.live_search_tickets, name="live_search_tickets"),
    path("live-search/", views.live_search_events, name="live_search"),

    path('organizer/create-event/', views.create_event_view, name='create_event'),
    path('event-created/', views.event_created_view, name='event_created'),
    path('event/', views.view_events_view, name='event'),
    path('event/<int:event_id>/edit/', views.edit_event_view, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event_view, name='delete_event'),
    path('event/<int:event_id>/bookmark/', views.add_bookmark_view, name='add_bookmark'),
    path('bookmarks/', views.bookmarks_view, name='bookmarks'),
    path('my-tickets/', views.ticket_owned_view, name='ticket_owned'),
    path('delete-ticket/<int:ticket_id>/', views.delete_ticket_view, name='delete_ticket'),
    path("live-search-organizer-events/", views.live_search_organizer_events, name="live_search_organizer_events"),
    path('logout/organizer/confirm/', views.confirmlogout_organizer_view, name='confirmlogout_organizer'),

    path('event/<int:event_id>/bookmark/confirmation/', views.confirmation_bookmark_view, name='confirmation_bookmark'),

    path('remove-bookmark/<int:event_id>/', views.remove_bookmark, name='remove_bookmark'),
    
    path("profile/", views.user_profile_view, name="user_profile"),

    path(
    'qr-code-sent/<str:price>/<str:balance>/',  # Use str instead of slug
    views.qr_code_sent_with_balance_view, 
    name='qr_code_sent_with_balance'
    ),

    
    path('qr-code-sent/', views.qr_code_sent_view, name='qr_code_sent'),

    # Forgot Password
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            extra_email_context={
                "brand_name": "Event CIT",
                "domain": getattr(settings, "DEFAULT_DOMAIN", "qreentry-7.onrender.com"),  # ✅ For Render domain
                "protocol": getattr(settings, "DEFAULT_PROTOCOL", "https"),  # ✅ Ensure HTTPS links
            },
            from_email="Event CIT <johnharleycruz592@gmail.com>",  # Sender name still works with SendGrid
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
