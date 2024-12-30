#!/bin/sh

# Run needed python commands.
python manage.py createcachetable
python manage.py migrate --noinput
python manage.py clear_cache --cache=default
python manage.py sync_roles
python manage.py wagtailsiteupdate hypha.test 8080

# Start gunicorn server.
gunicorn hypha.wsgi:application --env DJANGO_SETTINGS_MODULE=hypha.settings.production --threads 3 --reload  --bind 0.0.0.0:9001

exec "$@"
