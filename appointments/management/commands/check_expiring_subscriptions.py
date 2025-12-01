from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from appointments.models import UserSubscription
from appointments.email_utils import send_subscription_expiration_email, send_subscription_expired_email

class Command(BaseCommand):
    help = 'Checks for subscriptions that are about to expire or have expired and sends notifications'

    def handle(self, *args, **options):
        today = timezone.now().date()
        three_days_from_now = today + timedelta(days=3)

        # Check for subscriptions about to expire (within next 3 days)
        expiring_subscriptions = UserSubscription.objects.filter(
            is_active=True,
            end_date__lte=three_days_from_now,
            end_date__gt=today
        )

        for subscription in expiring_subscriptions:
            try:
                send_subscription_expiration_email(subscription.user, subscription)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully sent expiration notification to {subscription.user.username}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send expiration notification to {subscription.user.username}: {str(e)}'
                    )
                )

        # Check for subscriptions that have expired today
        expired_subscriptions = UserSubscription.objects.filter(
            is_active=True,
            end_date=today
        )

        for subscription in expired_subscriptions:
            try:
                # Send expired notification
                send_subscription_expired_email(subscription.user, subscription)
                # Update subscription status
                subscription.is_active = False
                subscription.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully sent expired notification to {subscription.user.username}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send expired notification to {subscription.user.username}: {str(e)}'
                    )
                ) 