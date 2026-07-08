#!/bin/bash
set -a; source .env; set +a
export USE_MYSQL=True
export DJANGO_SETTINGS_MODULE=car_crm.settings
export PYTHONPATH="/home/cameltech/Projects/Car Retail/NEW-final:$PYTHONPATH"
cd "/home/cameltech/Projects/Car Retail/NEW-final"
exec /home/cameltech/Projects/Car\ Retail/NEW-final/venv/bin/python manage.py runserver 0.0.0.0:8000
