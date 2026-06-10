#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Installing Python System Dependencies ---"
pip install -r requirements.txt

echo "--- Collecting Static Asset Canvas Injections ---"
python manage.py collectstatic --no-input

echo "--- Booting Production Gunicorn Cluster Engine ---"
# Replace 'scorpion_academy' with the actual folder name containing your root wsgi.py file
gunicorn scorpion_academy.wsgi:application --bind 0.0.0.0:$PORT