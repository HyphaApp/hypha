# Stand alone

## Standalone Server/VPS


## System Dependencies

* Git
* uv
* Python {{ versions.python.version }}
* Node {{ versions.node.version }}
* PostgreSQL {{ versions.postgres.version }}

### Get the code

Use `git` to fetch the code, this will create a `hypha/` directory.

```shell
git clone https://github.com/HyphaApp/hypha.git hypha
cd hypha
```

!!! info
    Everything from now on will happen inside the `hypha/` directory.


### Installing uv

[uv](https://docs.astral.sh/uv/) is an extremely fast Python package and project manager, written in Rust. A single tool to replace pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv, and more.

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Set up python virtual environment oand install python packages with uv

The uv sync command will create the virtual environment if it does not exist and install the python packages. For production we add `--frozen` so the `uv.lock` is not updated and `--no-default-frozens` so dev and docs are skipped.

```shell
uv sync --frozen --no-default-frozens
```

Run this command on each new deployment to update any packages.

By prepending all python and pip commands with `uv` they will automatically use the virtual environment and the correct python version.

!!! info
    While not recommended, pip can still be used to setup your Hypha environment. Just run ```python3 -m pip install -r requirements/<environment>.txt```


### Installing Node Version Manager

NodeJS versions have potential to change. To allow for ease of upgrading, it is recommended to use [Node Version Manager (nvm)](https://github.com/nvm-sh/nvm).

The following commands will install nvm and proceed to setup Node based off of the content of `.nvmrc`.

```shell
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
nvm install     # Install the Node version in .nvmrc
nvm use         # Use the Node version in .nvmrc
```

### Install Node packages

All the needed Node packages are listed in `package.json`. Install them with this command.

```shell
npm install
```

### The Postgres database

Postgresql is the database used. See <https://docs.djangoproject.com/en/stable/ref/settings/#databases>

We use `dj-database-url` so also see <https://github.com/jazzband/dj-database-url>

By default Hypha looks for a database with the name "hypha". Set `APP_NAME` to change the database name.

    APP_NAME = env.str('APP_NAME', 'hypha')
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            default=f'postgres:///{APP_NAME}'
        )
    }


### Running the app

The application needs a secret key: `export SECRET_KEY='SOME SECRET KEY HERE'`.

To begin with, set the `export SECURE_SSL_REDIRECT=false` to prevent SSL redirect. When you've set up SSL for your server, you can change that setting later.

Then use the following commands to test run the server:

```shell
npm run build
uv python manage.py collectstatic --noinput
uv python manage.py createcachetable
uv python manage.py migrate --noinput
uv python manage.py sync_roles
uv python manage.py clear_cache --cache=default
uv python manage.py createsuperuser
uv python manage.py wagtailsiteupdate apply.server.domain 80
uv python manage.py runserver
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

The Django Administration panel can be accessed via `https://apply.server.domain/django-admin/` \(use the email address and password you set in the `python manage.py createsuperuser` step above.\)

The Apply dashboard is here: `http://apply.server.domain/dashboard/`. The Wagtail admin: `http://apply.server.domain/admin`

### Settings

Here is a list of settings that can be set as environment variables or in a `hypha/settings/local.py` file.

**None optional:**

```text
SECRET_KEY:                                    [KEY]
DJANGO_SETTINGS_MODULE:                        hypha.settings.production
PRIMARY_HOST:                                  www.example.org
EMAIL_HOST:                                    example.org
ORG_EMAIL:                                     hello@example.org
ORG_GUIDE_URL:                                 https://guide.example.org/
ORG_LONG_NAME:                                 Long name of your organisation
ORG_SHORT_NAME:                                Short org name
SERVER_EMAIL:                                  app@example.org
SEND_MESSAGES:                                 true
```

**Passkeys:**

To activate passkeys in production you must set at least `WEBAUTHN_RP_ID` to the relying party domain, e.g. "example.com" (no port, no scheme).


**Turn on Hypha features that are off by default:**

```text
GIVE_STAFF_LEAD_PERMS:                         true
HIDE_IDENTITY_FROM_REVIEWERS:                  true
HIDE_STAFF_IDENTITY:                           true
PROJECTS_AUTO_CREATE:                          true
PROJECTS_ENABLED:                              true
STAFF_UPLOAD_CONTRACT:                         true
SUBMISSIONS_ARCHIVED_ACCESS_STAFF:             true
SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF:        true
SUBMISSIONS_DRAFT_ACCESS_STAFF:                true
SUBMISSIONS_DRAFT_ACCESS_STAFF_ADMIN:          true
TRANSITION_AFTER_ASSIGNED:                     true
TRANSITION_AFTER_REVIEWS:                      true
```

Then there are settings for S3 buckets, Slack, Mailgun, Authentication, multi languages etc. See files in  `hypha/settings`.
