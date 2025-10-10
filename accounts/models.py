from django.db import models

# Create your models here.

from django.contrib.auth.models import User

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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_name
    

    