# Build Python app
FROM python:3.6.4-stretch

WORKDIR /app
ENV PYTHONPATH /app

# Install non-python dependencies
RUN apt-get update -y &&\
    apt-get install -y apt-transport-https rsync &&\
    # Install Node 8
    curl -sL https://deb.nodesource.com/setup_8.x | bash - &&\
    apt-get install -y nodejs &&\
    # Remove apt cache
    rm -rf /var/lib/apt/lists/*

## Install requirements - done in a separate step so Docker can cache it.
COPY requirements.txt /
RUN pip install -r /requirements.txt

# Install Yarn dependencies
COPY ./opentech/static_src/package.json ./opentech/static_src/package-lock.json /app/opentech/static_src/
RUN npm install --prefix /app/opentech/static_src/ --frozen-lockfile

## Compile static files
COPY ./opentech/static_src/ /app/opentech/static_src/
RUN npm run build:prod --prefix /app/opentech/static_src/

## Install application code.
COPY . .

## Install assets
RUN SECRET_KEY=none django-admin.py collectstatic --noinput --clear --settings=opentech.settings.production

## Run application
EXPOSE 8000
CMD uwsgi --disable-logging --chdir /app --threads 2 --http-socket :8000 --wsgi-file opentech/wsgi.py