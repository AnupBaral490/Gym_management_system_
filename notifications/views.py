from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Notification, UserNotification
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

# Create your views here.

@login_required
@user_passes_test(lambda u: u.is_staff)  # Only staff members can send notifications
def send_notification(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type')
        
        if not all([title, message, notification_type]):
            messages.error(request, 'Please fill in all fields')
            return redirect('notifications:send_notification')
        
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
                
                messages.success(request, f'Notification sent successfully to {users.count()} users!')
                return redirect('notifications:send_notification')
                
        except Exception as e:
            messages.error(request, f'Error sending notification: {str(e)}')
            return redirect('notifications:send_notification')
    
    return render(request, 'notifications/send_notification.html')

@login_required
def user_notifications(request):
    notifications = UserNotification.objects.filter(
        user=request.user,
        notification__is_active=True
    ).order_by('-created_at')
    
    return render(request, 'notifications/user_notifications.html', {
        'notifications': notifications
    })

@login_required
@require_POST
def mark_as_read(request, notification_id):
    try:
        user_notification = UserNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        user_notification.is_read = True
        user_notification.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
            
        messages.success(request, 'Notification marked as read')
    except UserNotification.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error'}, status=404)
            
        messages.error(request, 'Notification not found')
    
    return redirect('notifications:user_notifications')
