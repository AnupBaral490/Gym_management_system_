from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('send/', views.send_notification, name='send_notification'),
    path('user/', views.user_notifications, name='user_notifications'),
    path('mark-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
] 