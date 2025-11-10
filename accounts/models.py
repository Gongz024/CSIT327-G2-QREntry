from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png')

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100)
    qr_code_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.event_name}"
    

# ✅ Event model
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


# ✅ Bookmark model (placed OUTSIDE the Event class)
class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookmarked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bookmarked {self.event.event_name}"


# ✅ Payment method integration model
class Order(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=255)
    event = models.ForeignKey("Event", on_delete=models.CASCADE, null=True, blank=True)
    amount = models.IntegerField(help_text="Amount in centavos", default=0)  # PHP centavos
    currency = models.CharField(max_length=10, default="PHP")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    paymongo_link_id = models.CharField(max_length=255, null=True, blank=True)
    paymongo_checkout_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order #{self.id} - {self.event_name} - {self.user}"
