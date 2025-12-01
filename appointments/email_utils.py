from django.core.mail import send_mail
from django.conf import settings

def send_subscription_email(user, plan, time_slot, start_date, end_date):
    subject = "Your Gym Subscription Details"
    message = (
        f"Hello {user.username},\n\n"
        f"Thank you for subscribing to the {plan.name}.\n"
        f"Session: {time_slot.get_session_display()} ({time_slot.start_time.strftime('%I:%M %p')} to {time_slot.end_time.strftime('%I:%M %p')})\n"
        f"Start Date: {start_date}\n"
        f"End Date: {end_date}\n\n"
        "We look forward to seeing you at the gym!\n"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def send_appointment_email(user, appointment):
    subject = "Your Gym Appointment Confirmation"
    time_slot = appointment.time_slot
    message = (
        f"Hello {user.username},\n\n"
        f"Your appointment is confirmed for {appointment.date}.\n"
        f"Session: {time_slot.get_session_display()} ({time_slot.start_time.strftime('%I:%M %p')} to {time_slot.end_time.strftime('%I:%M %p')})\n\n"
        "See you at the gym!"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def send_subscription_expiration_email(user, subscription):
    subject = "Your Gym Subscription is Expiring Soon"
    message = (
        f"Hello {user.username},\n\n"
        f"Your subscription to {subscription.plan.name} will expire on {subscription.end_date}.\n"
        f"To continue enjoying our services, please renew your subscription.\n\n"
        f"Current Plan Details:\n"
        f"- Plan: {subscription.plan.name}\n"
        f"- Time Slot: {subscription.time_slot.get_session_display()} ({subscription.time_slot.start_time.strftime('%I:%M %p')} to {subscription.time_slot.end_time.strftime('%I:%M %p')})\n\n"
        "Visit our website to renew your subscription and maintain your fitness journey!\n\n"
        "Best regards,\n"
        "Devi's Gym Nepal Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def send_subscription_expired_email(user, subscription):
    subject = "Your Gym Subscription Has Expired"
    message = (
        f"Hello {user.username},\n\n"
        f"Your subscription to {subscription.plan.name} has expired on {subscription.end_date}.\n"
        f"To continue your fitness journey with us, please renew your subscription.\n\n"
        f"Previous Plan Details:\n"
        f"- Plan: {subscription.plan.name}\n"
        f"- Time Slot: {subscription.time_slot.get_session_display()} ({subscription.time_slot.start_time.strftime('%I:%M %p')} to {subscription.time_slot.end_time.strftime('%I:%M %p')})\n\n"
        "Visit our website to renew your subscription and maintain your fitness journey!\n\n"
        "Best regards,\n"
        "Devi's Gym Nepal Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email]) 