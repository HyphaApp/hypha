release: python manage.py migrate --noinput && python manage.py clear_cache --cache=default --cache=wagtailcache
web: gunicorn opentech.wsgi:application --log-file -
