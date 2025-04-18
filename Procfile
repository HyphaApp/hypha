release: python manage.py migrate --noinput && python manage.py clear_cache --cache=default && python manage.py sync_roles
web: gunicorn hypha.wsgi:application --log-file -
worker: celery worker --app=hypha.celery --autoscale=6,2 --events