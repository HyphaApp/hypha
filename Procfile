release: python manage.py migrate --noinput && python manage.py clear_cache --cache=default && python manage.py sync_roles
web: gunicorn hypha.wsgi:application --log-file -
worker: celery --app=hypha.celery worker --autoscale=6,2 --events
