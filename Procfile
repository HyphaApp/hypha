release: python manage.py migrate --noinput
web: gunicorn opentech.wsgi:application --log-file -
