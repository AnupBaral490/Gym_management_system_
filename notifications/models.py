from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    notification_type = models.CharField(max_length=50, choices=[
        ('holiday', 'Holiday'),
        ('event', 'Special Event'),
        ('update', 'Important Update'),
        ('general', 'General')
    ])

    def __str__(self):
        return self.title

class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'notification')

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"
