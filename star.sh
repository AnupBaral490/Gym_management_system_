
#!/bin/bash
gunicorn gym_management_system.wsgi:application --bind 0.0.0.0:$PORT
