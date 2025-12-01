from django.urls import path
from . import views
from .views import my_certificates, my_badges, leaderboard
from .views import generate_certificate
from django.conf import settings
from django.conf.urls.static import static
from .otp_views import request_otp, verify_otp, reset_password

from appointments.views import full_logout
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('full_logout/', views.full_logout, name='full_logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('workout-log/', views.workout_log, name='workout_log'),
    path('workout-history/', views.workout_history, name='workout_history'),
    path('track-progress/', views.track_progress, name='track_progress'),
    path('progress-history/', views.progress_history, name='progress_history'),
    path('my-certificates/', my_certificates, name='my_certificates'),
    path('my-badges/', my_badges, name='my_badges'),
    path('leaderboard/', leaderboard, name='leaderboard'),
    path('generate-certificate/<str:username>/', generate_certificate, name='generate_certificate'),
    path('contact/', views.contact, name='contact'),
    path('personal-training/', views.personal_training, name='personal_training'),
    path('yoga-classes/', views.yoga_classes, name='yoga_classes'),
    path('strength-training/', views.strength_training, name='strength_training'),
    path('nutrition/', views.nutrition, name='nutrition'),
    path('steam/', views.steam, name='steam'),
    path('bmi/', views.bmi, name='bmi'),
    path('newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),
    path('upload-photo/', views.upload_photo, name='upload_photo'),
    path('request-otp/', request_otp, name='request_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('reset-password/<str:email>/', reset_password, name='reset_password'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
