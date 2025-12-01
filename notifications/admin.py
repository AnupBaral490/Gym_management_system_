from django.contrib import admin
from .models import Notification, UserNotification
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib import messages
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.db.models import Count, F, ExpressionWrapper, FloatField
from django.utils import timezone
from datetime import timedelta

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'created_at', 'is_active')
    list_filter = ('notification_type', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    actions = ['send_to_all_users']
    change_list_template = 'admin/notifications/notification/change_list.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Calculate statistics
        total_notifications = Notification.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Calculate read rate
        total_user_notifications = UserNotification.objects.count()
        read_notifications = UserNotification.objects.filter(is_read=True).count()
        read_rate = round((read_notifications / total_user_notifications * 100) if total_user_notifications > 0 else 0, 1)
        
        # Get recent activity
        recent_notifications = Notification.objects.order_by('-created_at')[:5]
        
        # Get recent activity text
        if recent_notifications:
            last_notification = recent_notifications[0]
            recent_activity = f"Last notification: {last_notification.title}"
        else:
            recent_activity = "No recent activity"
        
        extra_context.update({
            'total_notifications': total_notifications,
            'active_users': active_users,
            'read_rate': read_rate,
            'recent_activity': recent_activity,
            'recent_notifications': recent_notifications,
        })
        
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-notification/', self.send_notification_view, name='send-notification'),
        ]
        return custom_urls + urls

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def send_notification_view(self, request):
        if request.method == 'POST':
            title = request.POST.get('title')
            message = request.POST.get('message')
            notification_type = request.POST.get('notification_type')
            
            if not all([title, message, notification_type]):
                self.message_user(request, "Please fill in all fields", level=messages.ERROR)
                return redirect('admin:send-notification')
            
            try:
                with transaction.atomic():
                    # Create the notification
                    notification = Notification.objects.create(
                        title=title,
                        message=message,
                        notification_type=notification_type
                    )
                    
                    # Get all active users
                    users = User.objects.filter(is_active=True)
                    
                    # Create UserNotification entries for all users in bulk
                    user_notifications = [
                        UserNotification(user=user, notification=notification)
                        for user in users
                    ]
                    UserNotification.objects.bulk_create(user_notifications)
                    
                    self.message_user(request, f"Notification sent successfully to {users.count()} users!")
                    return redirect('admin:notifications_notification_changelist')
                    
            except Exception as e:
                self.message_user(request, f"Error sending notification: {str(e)}", level=messages.ERROR)
                return redirect('admin:send-notification')
        
        return render(request, 'admin/notifications/send_notification.html', {
            'title': 'Send Notification to All Users',
            'opts': self.model._meta,
        })

    def send_to_all_users(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(request, "Please select only one notification to send.", level=messages.ERROR)
            return

        notification = queryset.first()
        try:
            with transaction.atomic():
                # Get all active users
                users = User.objects.filter(is_active=True)
                
                # Create UserNotification entries for all users in bulk
                user_notifications = [
                    UserNotification(user=user, notification=notification)
                    for user in users
                ]
                UserNotification.objects.bulk_create(user_notifications)
                
                self.message_user(request, f"Notification sent successfully to {users.count()} users!")
        except Exception as e:
            self.message_user(request, f"Error sending notification: {str(e)}", level=messages.ERROR)

    send_to_all_users.short_description = "Send selected notification to all users"

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'notification__title')
