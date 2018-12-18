#!/bin/bash

PROJECT_NAME=$1
MODULE_NAME=$2

PROJECT_DIR=/vagrant
VIRTUALENV_DIR=/home/vagrant/.virtualenvs/$PROJECT_NAME

PYTHON=$VIRTUALENV_DIR/bin/python
PIP=$VIRTUALENV_DIR/bin/pip

# Upgrade to postgres 10
apt-get update -y
apt-get remove -y --purge postgresql-*
apt-get install -y postgresql-10 postgresql-client-10 postgresql-contrib-10
su - postgres -c "createuser -s vagrant"

# Create database

su - vagrant -c "createdb $MODULE_NAME"

# Virtualenv setup for project
su - vagrant -c "virtualenv --python=python3 $VIRTUALENV_DIR"

su - vagrant -c "echo $PROJECT_DIR > $VIRTUALENV_DIR/.project"


# Upgrade PIP itself
su - vagrant -c "$PIP install --upgrade pip"

# Upgrade setuptools (for example html5lib needs 1.8.5+)
su - vagrant -c "$PIP install --upgrade six setuptools"

# Install PIP requirements
su - vagrant -c "$PIP install -r $PROJECT_DIR/requirements.txt"


# Set execute permissions on manage.py as they get lost if we build from a zip file
chmod a+x $PROJECT_DIR/manage.py


# running migrations here is typically not necessary because of fab pull_data
# su - vagrant -c "$PYTHON $PROJECT_DIR/manage.py migrate --noinput"


# Add a couple of aliases to manage.py into .bashrc
cat << EOF >> /home/vagrant/.bashrc
export PYTHONPATH=$PROJECT_DIR
export DJANGO_SETTINGS_MODULE=$MODULE_NAME.settings.dev

alias dj="django-admin.py"
alias djrun="dj runserver 0.0.0.0:8000"
alias djrunp="dj runserver_plus 0.0.0.0:8000"

source $VIRTUALENV_DIR/bin/activate
export PS1="[$PROJECT_NAME \W]\\$ "
cd $PROJECT_DIR
EOF

# Install node.js and npm
su - vagrant -c "curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -"
su - vagrant -c "sudo apt-get install -y nodejs"

# Build the static files
su - vagrant -c "sudo npm install -g gulp-cli"
su - vagrant -c "cd $PROJECT_DIR; npm install"
su - vagrant -c "cd $PROJECT_DIR; gulp deploy"
