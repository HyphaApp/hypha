release: python manage.py migrate --noinput && python manage.py clear_cache --cache=default && python manage.py sync_roles
web: gunicorn --preload --max-requests 1000 --max-requests-jitter 50  hypha.wsgi:application --log-file -
worker: celery --app=hypha.celery worker --autoscale=6,2 --events
