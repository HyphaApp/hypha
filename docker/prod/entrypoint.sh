#!/bin/sh

# Run needed python commands.
python manage.py createcachetable
python manage.py migrate --noinput
python manage.py clear_cache --cache=default
python manage.py sync_roles

exec "$@"
