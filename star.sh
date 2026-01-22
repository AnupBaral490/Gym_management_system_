#!/bin/bash
# Start Django with Gunicorn on Render
gunicorn Gym_management_system.wsgi:application --bind 0.0.0.0:$PORT
