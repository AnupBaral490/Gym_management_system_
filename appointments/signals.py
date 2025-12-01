from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:
        subject = "Welcome to Devi's Gym Pokhara"
        message = f'Hi {instance.username},\n\nWelcome to our Devi\'s Gym POkhara-17 Chhorepatan. Thank you for registering.\n\nBest regards,\nGym Appointment Team'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )