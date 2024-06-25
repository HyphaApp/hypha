release: python manage.py migrate --noinput && python manage.py clear_cache --cache=default
web: gunicorn hypha.wsgi:application --log-file -
