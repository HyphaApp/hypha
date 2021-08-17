#!/bin/sh

#npm install --quiet
gulp deploy

#pip3 install --quiet -r requirements-dev.txt
python3 manage.py createcachetable
python3 manage.py collectstatic --noinput --verbosity=0
python3 manage.py migrate
python3 manage.py wagtailsiteupdate domain.org apply.domain.org
gunicorn hypha.wsgi:application --env DJANGO_SETTINGS_MODULE=hypha.settings.production --reload  --bind 0.0.0.0:9001

exec "$@"
