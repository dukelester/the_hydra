#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${LOAD_DEMO_DATA:-false}" = "true" ]; then
  python manage.py load_demo_data --reset
fi

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
username = '${DJANGO_SUPERUSER_USERNAME}'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, '${DJANGO_SUPERUSER_EMAIL:-admin@example.com}', '${DJANGO_SUPERUSER_PASSWORD}')
    print('Created superuser', username)
"
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --timeout 60
