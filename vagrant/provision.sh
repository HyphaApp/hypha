#!/bin/bash

PROJECT_NAME=$1
MODULE_NAME=$2

PROJECT_DIR=/vagrant
PIPENV_DIR="/home/vagrant/.local/bin"

# Install pipenv
su - vagrant -c "pip3 install pipenv --user"

su - vagrant -c "echo \"export PATH=$PATH:$PIPENV_DIR\" > /home/vagrant/.bash_profile"
su - vagrant -c "source ~/.bash_profile"

# Setup environment and install
su - vagrant -c "cd /vagrant; pipenv install --dev"


# Create database
su - vagrant -c "createdb $MODULE_NAME"

# Set execute permissions on manage.py as they get lost if we build from a zip file
chmod a+x $PROJECT_DIR/manage.py


# running migrations here is typically not necessary because of fab pull_data
# su - vagrant -c "pipenv run django-admin.py migrate --noinput"


# Add a couple of aliases to manage.py into .bashrc
cat << EOF > /home/vagrant/.bash_profile
export PYTHONPATH=$PROJECT_DIR
export DJANGO_SETTINGS_MODULE=$MODULE_NAME.settings.dev

alias dj="pipenv run django-admin.py"
alias djrun="dj runserver 0.0.0.0:8000"
alias djrunp="dj runserver_plus 0.0.0.0:8000"

export PS1="[$PROJECT_NAME \W]\\$ "

# Pipenv settings
export PATH=$PATH:$PIPENV_DIR
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

cd $PROJECT_DIR
EOF

# Install node.js and npm
su - vagrant -c "curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -"
su - vagrant -c "sudo apt-get install -y nodejs"

su - vagrant -c "curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -"
su - vagrant -c "echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list"
su - vagrant -c "sudo apt-get update && sudo apt-get install yarn"

# Build the static files
su - vagrant -c "cd $PROJECT_DIR/$MODULE_NAME/static_src; yarn install"
su - vagrant -c "cd $PROJECT_DIR/$MODULE_NAME/static_src; yarn build"
