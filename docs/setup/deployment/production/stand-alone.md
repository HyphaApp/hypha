# Stand Alone

## Standalone Server/VPS


## System Dependencies

* Git
* Python {{ versions.python.version }}
* Node {{ versions.node.version }}
* PostgreSQL {{ versions.postgres.version }}

!!! info
    On Linux install them with your normal package manager. On macOS [Homebrew] is an excellent option. For Windows [Chocolatey](https://chocolatey.org/) seems popular but we have no experience with Windows. 
    
    This project ships with `.python-version` and `.nvmrc` to support **[pyenv]** and **[nvm]**. You can use it to setup the correct versions of Python and Node required for this project.

## Basic installation steps

<!-- NOTE! Before updating the install steps here, ensure they are reflected in the development install as well -->

=== "Debian"

    This process was tested on **Ubuntu {{ versions.tested_ubuntu.version }}**. It should work on any Debian-based system.

    Install Python pip, venv & PostgreSQL:

    ```shell
    sudo apt install -y \
        python3-pip python3-venv \
        postgresql postgresql-contrib {{ versions.postgres.packages.debian }}
    ```

=== "Fedora"

    This process was tested on **Fedora {{ versions.tested_fedora.version }}**. It should work on RHEL as well.

    Install Python pip, venv & PostgreSQL:

    ```shell
    sudo dnf module -y reset postgresql
    sudo dnf module -y enable postgresql:{{ versions.postgres.version }}
    sudo dnf install -y \
        python3-pip gcc python3-devel \
        {{ versions.postgres.packages.fedora }} postgresql-contrib {{ versions.postgres_devel.packages.fedora }}
    sudo /usr/bin/postgresql-setup --initdb
    ```


=== "macOS"

    This process was tested on **macOS {{ versions.tested_macos.version }}**.

    Install Python pip, venv & PostgreSQL:

    ```shell
    brew install {{ versions.python.packages.macos }} 
    brew install {{ versions.postgres.packages.macos }}
    brew services start {{ versions.postgres.packages.macos }}
    ```

----

### Get the code

Use `git` to fetch the code, this will create a `hypha/` directory.

```shell
git clone https://github.com/HyphaApp/hypha.git hypha
cd hypha
```

### Installing Node Version Manager

NodeJS versions have potential to change. To allow for ease of upgrading, it is recommended to use [Node Version Manager (nvm)](https://github.com/nvm-sh/nvm).

The following commands will install nvm and proceed to setup Node based off of the content of `.nvmrc`.

```shell
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
nvm install     # Install the Node version in .nvmrc
nvm use         # Use the Node version in .nvmrc
```

### Python virtual environment

Create the virtual environment, specify the python binary to use and the directory. Then source the activate script to activate the virtual environment. The last line tells Django what settings to use.

```shell
python3 -m venv venv/hypha
source venv/hypha/bin/activate
export DJANGO_SETTINGS_MODULE=hypha.settings.production
```

Inside your activated virtual environment you will use plain `python` and `pip` commands. Everything inside the virtual environment is python 3 since we specified that when we created it.

### Install Python packages

Next, install the required packages using:

```shell
python3 -m pip install -r requirements.txt
```

### Install Node packages

All the needed Node packages are listed in `package.json`. Install them with this command.

```text
npm install
```

### The Postgres database

Postgresql is the database used. The following commands will start the Postgresql service and login to the postgres superuser:

```shell
sudo service postgresql start
sudo su - postgres
```

then, enter the postgresql cli with:

```shell
psql
```

In the CLI use these commands to create the initial hypha database, and add a superuser (replacing `replace_with_username` with the user account that will be running hypha):

```sql
CREATE DATABASE hypha;
CREATE USER replace_with_username WITH SUPERUSER LOGIN;
```

Confirm that this user has trust access in `pg\_hba.conf`. These settings can be restricted later as required.

To exit out of both the psql interface & the postgres user session, do `Ctrl + D` twice.

### Running the app

The application needs a secret key: `export SECRET_KEY='SOME SECRET KEY HERE'`.

To begin with, set the `export SECURE_SSL_REDIRECT=false` to prevent SSL redirect. When you've set up SSL for your server, you can change that setting later.

Then use the following commands to test run the server:

```shell
npm run build
python manage.py collectstatic --noinput
python manage.py createcachetable
python manage.py migrate --noinput
python manage.py clear_cache --cache=default --cache=wagtailcache
python manage.py createsuperuser
python manage.py wagtailsiteupdate apply.server.domain 80
python manage.py runserver
```

\(runs development server at [http://127.0.0.1:8000](http://127.0.0.1:8000)\)

You should see the home page of the server. That's great. You can stop the server, and then we can then take the next steps.

### Deploy with nginx/gunicorn

Make sure gunicorn is installed \(it should be\). Do a test run with gunicorn: `gunicorn --bind 0.0.0.0:<some port> hypha.wsgi:application` This might not work. It's OK if it doesn't work - you can go on anyway.

To make gunicorn start automatically with systemd see [https://docs.gunicorn.org/en/stable/deploy.html\#systemd](https://docs.gunicorn.org/en/stable/deploy.html#systemd).

Set up DNS so that apply.server.domain points to the server you've installed the application. Install nginx if you haven't already \(`sudo apt-get install nginx`\). You'll need to add a new config file for nginx in /etc/nginx/sites-available:


```text
server {
    listen 80;
    server_name apply.server.domain;

    client_max_body_size 2621440;

    location /media/ {
        alias /path/to/application/hypha/media/;
    }

    location /static/ {
        alias /path/to/application/hypha/static/;
    }

    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

The `client_max_body_size` configuration directive is very important. Hypha uploads files to the server in 2.5MB chunks. However, by default, nginx limits uploads to 1MB chunks. The result is that users of a Hypha system running "behind" nginx will see file upload failures for any file larger than 1MB. Using the `client_max_body_size` directive in the nginx `server` context is, therefore, required to make it possible for users to upload files that are bigger than 1MB in size.

Symbolically link these to sites-enabled: `sudo ln -s /etc/nginx/sites-available/public /etc/nginx/sites-enabled && sudo ln -s /etc/nginx/sites-available/apply /etc/nginx/sites-enabled`. Then restart nginx using `sudo systemctl restart nginx`.

**You should then be able to access your application at **[http://apply.server.domain](http://apply.server.domain)**

### Adding SSL using a Let's Encrypt certificate.

It's very easy to add SSL via a Let's Encrypt certificate.

See instructions at [https://certbot.eff.org](https://certbot.eff.org).

Follow the instructions, and you're done.

### Administration

The Django Administration panel can be accessed via [http://apply.server.domain/django-admin/](http://sapply.erver.domain/django-admin/) \(use the email address and password you set in the `python manage.py createsuperuser` step above.\)

The Apply dashboard is here: [http://apply.server.domain/dashboard/](http://apply.server.domain/dashboard/). The Wagtail admin: [http://apply.server.domain/admin](http://apply.server.domain/admin)

### settings

Here is a list of settings that can be set as environment variables or in a `hypha/settings/local.py` file.

**None optional:**

```text
API_BASE_URL:                                  https://example.org/api
CACHE_CONTROL_MAX_AGE:                         14400
COOKIE_SECURE:                                 true
DJANGO_SETTINGS_MODULE:                        hypha.settings.production
EMAIL_HOST:                                    example.org
ORG_EMAIL:                                     hello@example.org
ORG_GUIDE_URL:                                 https://guide.example.org/
ORG_LONG_NAME:                                 Long name of your organisation
ORG_SHORT_NAME:                                Short org name
PRIMARY_HOST:                                  www.example.org
PROJECTS_AUTO_CREATE:                          false
PROJECTS_ENABLED:                              true
SECRET_KEY:                                    [KEY]
SEND_MESSAGES:                                 true
SERVER_EMAIL:                                  app@example.org
```

**Optional:**

```text
ANYMAIL_WEBHOOK_SECRET:                        [KEY]
AWS_ACCESS_KEY_ID:                             [KEY]
AWS_DEFAULT_ACL:                               None
AWS_MIGRATION_ACCESS_KEY_ID:                   [KEY]
AWS_MIGRATION_BUCKET_NAME:                     backup.example.org
AWS_MIGRATION_SECRET_ACCESS_KEY:               [KEY]
AWS_PRIVATE_BUCKET_NAME:                       private.example.org
AWS_PUBLIC_BUCKET_NAME:                        public.example.org
AWS_PUBLIC_CUSTOM_DOMAIN:                      public.example.org
AWS_QUERYSTRING_EXPIRE:                        600
AWS_SECRET_ACCESS_KEY:                         [KEY]
AWS_STORAGE_BUCKET_NAME:                       public.example.org
BASIC_AUTH_ENABLED:                            true
BASIC_AUTH_LOGIN:                              [USER]
BASIC_AUTH_PASSWORD:                           [PASS]
BASIC_AUTH_WHITELISTED_HTTP_HOSTS:             example.org
CLOUDFLARE_API_ZONEID:                         [KEY]
CLOUDFLARE_BEARER_TOKEN:                       [KEY]
MAILGUN_API_KEY:                               [KEY]
SEND_READY_FOR_REVIEW:                         false
SLACK_DESTINATION_ROOM:                        #notify
SLACK_DESTINATION_ROOM_COMMENTS:               #notes
SLACK_DESTINATION_URL:                         https://slackbot-example.org/incoming/[KEY]
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY:                 [KEY]
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET:              [KEY]
SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS: example.org
```

