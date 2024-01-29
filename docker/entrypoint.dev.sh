#!/bin/sh

# Install node packages and run build command.
npm install --quiet
npm run dev:build

# Run needed python commands.
python3 manage.py createcachetable
#python3 manage.py collectstatic --noinput --verbosity=0
python3 manage.py migrate
python3 manage.py wagtailsiteupdate hypha.test 8090

# Start gunicorn server.
gunicorn hypha.wsgi:application --env DJANGO_SETTINGS_MODULE=hypha.settings.dev --reload  --bind 0.0.0.0:9001

exec "$@"
