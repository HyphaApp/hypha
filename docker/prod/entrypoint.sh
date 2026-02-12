#!/bin/sh

# Run needed python commands.
python manage.py createcachetable
python manage.py migrate --noinput
python manage.py clear_cache --cache=default
python manage.py sync_roles

# Start gunicorn server.
gunicorn hypha.wsgi:application --env DJANGO_SETTINGS_MODULE=hypha.settings.production --worker-tmp-dir /dev/shm --workers=2 --threads=4 --worker-class=gthread  --bind 0.0.0.0:8000

exec "$@"
