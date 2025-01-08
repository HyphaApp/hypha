#!/usr/bin/env bash
set -e

# Run needed python commands.
python manage.py createcachetable
python manage.py migrate --noinput
python manage.py clear_cache --cache=default
python manage.py sync_roles
python manage.py wagtailsiteupdate hypha.test 9001

# Run uv sync
uv sync

# Start dev server.
npm run watch &
python manage.py runserver_plus 0.0.0.0:9001

exec "$@"
