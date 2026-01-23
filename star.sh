
#!/bin/bash
gunicorn gym_appointment.wsgi:application --bind 0.0.0.0:$PORT
