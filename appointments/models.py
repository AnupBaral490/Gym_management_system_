from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, time
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        (1, '1 Month'),
        (2, '2 Months'),
        (3, '3 Months'),
        (12, '1 Year'),
    ]
    
    name = models.CharField(max_length=100)
    duration_months = models.IntegerField(choices=DURATION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_duration_months_display()}"

class TimeSlot(models.Model):
    SESSION_CHOICES = [
        ('morning', 'Morning Session – 6:00 AM to 10:00 AM'),
        ('afternoon', 'Afternoon Session – 12:00 PM to 4:00 PM'),
        ('evening', 'Evening Session – 5:00 PM to 9:00 PM'),
    ]
    
    session = models.CharField(max_length=20, choices=SESSION_CHOICES, null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def clean(self):
        if self.session:
            # Ensure time slot is within the session hours
            if self.session == 'morning':
                if not (time(6, 0) <= self.start_time <= time(10, 0)):
                    raise ValidationError("Morning session must be between 6:00 AM and 10:00 AM")
            elif self.session == 'afternoon':
                if not (time(12, 0) <= self.start_time <= time(16, 0)):
                    raise ValidationError("Afternoon session must be between 12:00 PM and 4:00 PM")
            elif self.session == 'evening':
                if not (time(17, 0) <= self.start_time <= time(21, 0)):
                    raise ValidationError("Evening session must be between 5:00 PM and 9:00 PM")

    def __str__(self):
        if self.session:
            return f"{self.get_session_display()}"
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=30 * self.plan.duration_months)
        # Only activate subscription if payment is verified
        if self.payment and self.payment.payment_status == 'verified':
            self.is_active = True
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('verified', 'Verified')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_screenshot = models.ImageField(upload_to='payment_screenshots/', null=True, blank=True)
    transaction_code = models.CharField(max_length=100, blank=True, null=True)
    verification_notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.payment_status}"

class PaymentQRCode(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('bank_transfer', 'Bank Transfer'),
        ('other', 'Other')
    ]
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    qr_code_image = models.ImageField(upload_to='payment_qr_codes/')
    account_details = models.TextField(help_text="Account number, UPI ID, or other payment details")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_payment_method_display()} - {self.account_details}"

class Appointment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user_subscription = models.ForeignKey('UserSubscription', on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )

    class Meta:
        unique_together = ('user', 'date')  # Only one appointment per user per day

    def clean(self):
        if self.user_subscription:
            # Check if the date is a Saturday
            if self.date.weekday() == 5:  # 5 represents Saturday
                raise ValidationError("Gym is closed on Saturdays")
            
            # Check if the appointment is within the subscription period
            if not (self.user_subscription.start_date <= self.date <= self.user_subscription.end_date):
                raise ValidationError("Appointment date must be within subscription period")
            
            # Removed the time slot matching requirement

    def __str__(self):
        return f"{self.user.username} - {self.date} {self.time_slot}"

class Exercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category_choices = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility')
    ]
    category = models.CharField(max_length=20, choices=category_choices)
    
    def __str__(self):
        return self.name

class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s workout on {self.date}"

class ExerciseLog(models.Model):
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.IntegerField()
    reps = models.IntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        if self.exercise.category == 'cardio':
            return f"{self.exercise.name} - {self.duration_minutes} minutes"
        return f"{self.exercise.name} - {self.sets}x{self.reps} @ {self.weight}kg"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    body_fat = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Body fat percentage")
    chest = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Chest measurement in cm")
    waist = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Waist measurement in cm")
    arms = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Arms measurement in cm")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username}'s progress on {self.date}"

class PersonalBest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    reps = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in minutes")
    date_achieved = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'exercise']

    def __str__(self):
        return f"{self.user.username}'s PB for {self.exercise.name}"


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='certificates/')
    issued_date = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Certificate for {self.user.username}"

# Badge Model
class Badge(models.Model):
    BADGE_TYPES = [
        ('Course Completion', 'Course Completion'),
        ('Top Performer', 'Top Performer'),
        ('Consistency Award', 'Consistency Award'),
    ]
    
    POINTS_MAPPING = {
        'Course Completion': 50,
        'Top Performer': 100,
        'Consistency Award': 75,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES)
    awarded_date = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=0)  # New field for points

    def save(self, *args, **kwargs):
        """Assign points based on badge type before saving."""
        if not self.points:  # Assign points only if not already set
            self.points = self.POINTS_MAPPING.get(self.badge_type, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.badge_type} - {self.user.username} ({self.points} pts)"

# Leaderboard Model
class Leaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.points} points"
    

class Contact(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.CharField(max_length=10)
    desc = models.TextField()

    def __str__(self):
        return self.name
    

class NewsletterSignup(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    message = models.TextField(blank=True, null=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        null=True,
        blank=True,
        help_text="Upload a high-quality image (recommended size: 500x500px)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.profile_photo:
            # Ensure the image is saved in high quality
            img = Image.open(self.profile_photo)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            # Save the image with high quality
            output = BytesIO()
            img.save(output, format='JPEG', quality=95)
            output.seek(0)
            
            # Save the processed image
            self.profile_photo.save(
                self.profile_photo.name,
                ContentFile(output.read()),
                save=False
            )
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"