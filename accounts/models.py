# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

# --- Constants ---
DEFAULT_WALLET_BALANCE = Decimal("10000.00")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=DEFAULT_WALLET_BALANCE)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Ensure a Profile exists for every user
    profile, profile_created = Profile.objects.get_or_create(
        user=instance,
        defaults={'wallet_balance': DEFAULT_WALLET_BALANCE}
    )
    # Save to ensure defaults applied for new users
    if created or not profile_created:
        profile.save()


class Event(models.Model):
    EVENT_CATEGORIES = [
        ('Concerts', 'Concerts'),
        ('Sports', 'Sports'),
        ('Seminars', 'Seminars'),
        ('Others', 'Others'),
    ]

    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    event_name = models.CharField(max_length=100)
    event_description = models.TextField()
    event_category = models.CharField(max_length=50, choices=EVENT_CATEGORIES)
    event_venue = models.CharField(max_length=150)
    event_date = models.DateField()
    event_time_in = models.TimeField()
    event_time_out = models.TimeField()
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    ticket_limit = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_name


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    qr_code_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        # Defensive DB-level uniqueness to prevent duplicates
        unique_together = ('user', 'event')
        indexes = [
            models.Index(fields=['user', 'event']),
        ]

    def __str__(self):
        # Use event.event_name, Ticket has no event_name attribute
        return f"{self.user.username} - {self.event.event_name}"


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bookmarked {self.event.event_name}"
