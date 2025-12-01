import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_appointment.settings')
django.setup()

from django.contrib.auth.models import User

# Create a new superuser
username = 'gymadmin'
password = 'gym123456'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, 'admin@example.com', password)
    print(f"Superuser created successfully!")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"Superuser password updated successfully!")
