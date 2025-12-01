import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_appointment.settings')
django.setup()

from appointments.models import TimeSlot

# Create time slots for each session
sessions = [
    {
        'session': 'morning',
        'start_time': time(6, 0),
        'end_time': time(10, 0)
    },
    {
        'session': 'afternoon',
        'start_time': time(12, 0),
        'end_time': time(16, 0)
    },
    {
        'session': 'evening',
        'start_time': time(17, 0),
        'end_time': time(21, 0)
    }
]

for session_data in sessions:
    TimeSlot.objects.get_or_create(
        session=session_data['session'],
        defaults={
            'start_time': session_data['start_time'],
            'end_time': session_data['end_time'],
            'is_available': True
        }
    )

print("Created session-based time slots")
