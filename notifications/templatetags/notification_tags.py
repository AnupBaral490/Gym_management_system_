from django import template
from notifications.models import UserNotification

register = template.Library()

@register.inclusion_tag('notifications/notification_box.html')
def show_notifications(user):
    notifications = UserNotification.objects.filter(
        user=user,
        is_read=False,
        notification__is_active=True
    ).order_by('-created_at')
    return {'notifications': notifications} 