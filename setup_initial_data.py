import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_appointment.settings')
django.setup()

from appointments.models import TimeSlot, SubscriptionPlan

# Create time slots (2-hour slots)
time_slots_data = [
    (time(6, 0), time(8, 0)),   # 6:00 AM - 8:00 AM
    (time(8, 0), time(10, 0)),  # 8:00 AM - 10:00 AM
    (time(10, 0), time(12, 0)), # 10:00 AM - 12:00 PM
    (time(14, 0), time(16, 0)), # 2:00 PM - 4:00 PM
    (time(16, 0), time(18, 0)), # 4:00 PM - 6:00 PM
    (time(18, 0), time(20, 0)), # 6:00 PM - 8:00 PM
]

# Create time slots
for start, end in time_slots_data:
    TimeSlot.objects.get_or_create(
        start_time=start,
        end_time=end,
        defaults={'is_available': True}
    )
print("Created time slots")

# Create subscription plans
subscription_plans_data = [
    {
        'name': 'Monthly Package',
        'duration_months': 1,
        'price': 50.00,
        'description': 'Perfect for trying out our gym'
    },
    {
        'name': 'Quarterly Package',
        'duration_months': 3,
        'price': 135.00,
        'description': 'Our most popular package'
    },
    {
        'name': 'Bi-Monthly Package',
        'duration_months': 2,
        'price': 95.00,
        'description': 'Great value for short-term commitment'
    },
    {
        'name': 'Annual Package',
        'duration_months': 12,
        'price': 480.00,
        'description': 'Best value for long-term commitment'
    },
]

# Create subscription plans
for plan_data in subscription_plans_data:
    SubscriptionPlan.objects.get_or_create(
        name=plan_data['name'],
        defaults={
            'duration_months': plan_data['duration_months'],
            'price': plan_data['price'],
            'description': plan_data['description']
        }
    )
print("Created subscription plans")
