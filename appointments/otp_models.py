from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    purpose = models.CharField(max_length=20, choices=[
        ('registration', 'Registration'),
        ('password_reset', 'Password Reset')
    ])

    def __str__(self):
        return f"OTP for {self.email} - {self.purpose}"

    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        """Check if OTP is expired (10 minutes)"""
        return (timezone.now() - self.created_at).total_seconds() > 600  # 10 minutes 