from django.contrib import admin
from .models import TimeSlot, Appointment, SubscriptionPlan, UserSubscription
from .models import Certificate, Badge, Leaderboard, UserProfile
from appointments.models import Contact
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, F
from django.utils.html import format_html

from .models import NewsletterSignup, PaymentQRCode, Payment
from .email_utils import send_subscription_email

# Register your models here.

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'is_available')
    list_filter = ('is_available',)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_months', 'price')
    list_filter = ('duration_months',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'time_slot', 'is_active')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username',)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('get_profile_photo', 'username', 'email', 'first_name', 'last_name', 'is_staff')
    list_display_links = ('get_profile_photo', 'username')

    def get_profile_photo(self, obj):
        try:
            profile = obj.userprofile
            if profile.profile_photo:
                return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />', profile.profile_photo.url)
        except UserProfile.DoesNotExist:
            pass
        return format_html('<img src="/static/admin/img/icon-user-default.svg" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />')
    get_profile_photo.short_description = 'Photo'

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'time_slot', 'status', 'get_subscription_plan', 'get_amount_paid']
    list_filter = ['status', 'date']
    search_fields = ['user__username']
    
    def get_subscription_plan(self, obj):
        if obj.user_subscription and obj.user_subscription.plan:
            return obj.user_subscription.plan.name
        return "No Subscription"
    get_subscription_plan.short_description = 'Subscription Plan'

    def get_amount_paid(self, obj):
        if obj.user_subscription and obj.user_subscription.plan:
            return obj.user_subscription.plan.price
        return 0
    get_amount_paid.short_description = 'Amount Paid'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('revenue-dashboard/', self.admin_site.admin_view(self.revenue_dashboard), name='revenue-dashboard'),
        ]
        return custom_urls + urls

    def revenue_dashboard(self, request):
        # Calculate total revenue from active subscriptions
        total_revenue = UserSubscription.objects.filter(
            is_active=True
        ).aggregate(
            total=Sum('plan__price')
        )['total'] or 0

        # Calculate monthly revenue (active subscriptions this month)
        monthly_revenue = UserSubscription.objects.filter(
            is_active=True,
            start_date__year=2024,  # Current year
            start_date__month=4     # Current month
        ).aggregate(
            total=Sum('plan__price')
        )['total'] or 0

        # Calculate revenue by subscription plan
        revenue_by_plan = UserSubscription.objects.filter(
            is_active=True
        ).values(
            'plan__name'
        ).annotate(
            total=Sum('plan__price')
        )

        context = {
            'title': 'Revenue Dashboard',
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'revenue_by_service': revenue_by_plan,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/revenue_dashboard.html', context)

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'issued_date')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_type', 'awarded_date')

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'points')


admin.site.register(Contact)

admin.site.register(NewsletterSignup)

@admin.register(PaymentQRCode)
class PaymentQRCodeAdmin(admin.ModelAdmin):
    list_display = ('payment_method', 'account_details', 'is_active', 'created_at')
    list_filter = ('payment_method', 'is_active')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'amount', 'payment_status', 'created_at', 'payment_screenshot', 'transaction_code')
    list_filter = ('payment_status', 'subscription_plan')
    search_fields = ('user__username', 'transaction_code')
    readonly_fields = ('payment_screenshot',)
    actions = ['verify_payments', 'reject_payments']

    def verify_payments(self, request, queryset):
        for payment in queryset:
            payment.payment_status = 'verified'
            payment.save()
            # Activate all subscriptions linked to this payment
            for subscription in payment.usersubscription_set.all():
                subscription.is_active = True
                subscription.save()
                # Send email notification to user
                send_subscription_email(
                    subscription.user,
                    subscription.plan,
                    subscription.time_slot,
                    subscription.start_date,
                    subscription.end_date
                )
    verify_payments.short_description = "Mark selected payments as verified and activate subscription"

    def reject_payments(self, request, queryset):
        queryset.update(payment_status='failed')
    reject_payments.short_description = "Mark selected payments as failed"

    def save_model(self, request, obj, form, change):
        # Check if payment status is being set to 'verified'
        was_verified = False
        if change:
            old_obj = Payment.objects.get(pk=obj.pk)
            if old_obj.payment_status != 'verified' and obj.payment_status == 'verified':
                was_verified = True
        else:
            if obj.payment_status == 'verified':
                was_verified = True
        super().save_model(request, obj, form, change)
        if was_verified:
            # Activate all subscriptions linked to this payment and send email
            for subscription in obj.usersubscription_set.all():
                subscription.is_active = True
                subscription.save()
                send_subscription_email(
                    subscription.user,
                    subscription.plan,
                    subscription.time_slot,
                    subscription.start_date,
                    subscription.end_date
                )

admin.site.site_header = "Devi's Gym System"
admin.site.site_title = "Devi's Gym System Admin"
admin.site.index_title = "Welcome to Devi's Gym System Admin"
