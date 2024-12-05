# Stand Alone

In order to have get started with developing hypha locally, you'll need these
minimal setup, the setup may vary slightly for your base operating systems.

## System Dependencies

Make sure you have these things installed on your system:

* Git – [Installation Guide](https://git-scm.com/downloads)
* Python {{ versions.python.version }}
* Node {{ versions.node.version }}
* PostgreSQL {{ versions.postgres.version }} (with `libpq-dev` on Linux)

!!! info
    On Linux install them with your normal package manager. On macOS [Homebrew] is an excellent option. For Windows [Chocolatey](https://chocolatey.org/) seems popular but we have no experience with Windows. 
    
    This project ships with `.python-version` and `.nvmrc` to support **[pyenv]** and **[nvm]**. You can use it to setup the correct versions of Python and Node required for this project.


### Basic installation steps

<!-- NOTE! Before updating the install steps here, ensure they are reflected in the production install as well -->

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

## Get the code

Use `git` to fetch the code, this will create a `hypha/` directory.

```shell
git clone https://github.com/HyphaApp/hypha.git hypha
cd hypha
```

Now, create some local directories.

```shell
cd hypha
mkdir -p var/log media
```

NOTE: In production media is stored on AWS S3 but for local development you need a "media" directory. The `var/log` is used to store local logs, if configured.

!!! info
    Everything from now on will happen inside the `hypha/` directory.


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

## Compile JS & SCSS

Build all JS/CSS assets for development:

```shell
npm run dev:build
```

!!! info
    Hypha uses NodeJS to compile SCSS and JS from the `hypha/static_src/` directory. See the `package.json` 
    file for a complete list of commands.


## Add/Update Configuration

Hypha supports configuration via either a `local.py` or a `.env` file:

=== "Using `.env` file"

    Create an empty `.env` file at the root of the project:

    ```hl_lines="2"
    .
    ├── .env
    ├── manage.py
    ├── hypha
    │   ├── urls.py
    │   ├── settings/
    │   ├── ...
    ├── ...
    ```

    Open `.env` file and add your config:

    ```bash title="./.env"
    ALLOWED_HOSTS=hypha.test
    BASE_URL=http://hypha.test
    SECRET_KEY=<put-in-long-random-string>
    DATABASE_URL=postgres://localhost/hypha
    ```

=== "Using `local.py`"

    Copy the provided `local.py.example` file and rename it to `local.py`.

    ```shell
    cp -p hypha/settings/local.py.example hypha/settings/local.py
    ```

    ```hl_lines="10 11"
    .
    ├── manage.py
    ├── hypha
    │   ├── urls.py
    │   ├── settings
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── dev.py
    │   │   ├── django.py
    │   │   ├── local.py
    │   │   ├── local.py.example
    │   │   ├── production.py
    │   │   └── test.py
    │   ├── ...
    ├── ...
    ```
    
    Open and take a look at the `local.py`, it already has some sensible defaults and you can use this to override all the settings.

## Setup Database and Initial Data

Create an empty database:

```shell
createdb hypha
```

Ensure database name `hypha` is added to your `hypha/settings/local.py` or `.env`.

Let's create all the tables and schemas required by the project.

There are two ways to about it, you can either load demo data from  `/public/sandbox_db.dump` or start with empty tables.

=== "Load Demo Data"
    To load demo data run:

    ```shell
    pg_restore --verbose --clean  --if-exists --no-acl --no-owner \
                 --dbname=hypha public/sandbox_db.dump
    ```

    It's not always completely up to date so run:
    
    ```shell
    python3 manage.py migrate
    python3 manage.py sync_roles
    ```

=== "From Scratch"
    Create the cache tables.

    ```text
    python3 manage.py createcachetable
    ```

    Run all migrations to set up the database tables.

    ```text
    python3 manage.py migrate
    python3 manage.py sync_roles
    ```

!!! tip "Tips"

    - If `createdb`and `dropdb` are not available you will need to add the Postgres bin directory to your `path` or call the commands with complete path.
    - If you need to delete/drop the database, you can use `dropdb hypha`
    - On Linux you might need to run as the "postgres" user first when setting up Postgres. Use it to create the database and set up a database user.For local development I suggest creating a user with the same name as your account, then you will not need to specify it on every command.

        ```shell
        su - postgres
        createdb hypha
        createuser [your-account-name]
        ```

## Setup Sites

You will need two domain to run this app, used to serve the public and apply site on different domains

First, add these sites to the database:

```shell
$ python manage.py wagtailsiteupdate hypha.test 9001
```

Then, add this to your `/etc/hosts` file.

```text title="/etc/hosts"
127.0.0.1 hypha.test
```

Here we are setting the public site be served at http://hypha.test:9001.

!!! question "Is it safe to use .test?"
     The "[.test](https://en.wikipedia.org/wiki/.test)" TLD is safe to use, it's reserved for testing purposes. Feel free to use another name but then remember to use it in all the commands below.


## Create Login credentials

```shell
python3 manage.py createsuperuser
```

## Run Development Server

```shell
python3 manage.py runserver 0.0.0.0:9001 --settings=hypha.settings.dev
```

Alternatively, you can also use `make serve-django`


Now you should be able to access the site:

2. Apply Site: [http://hypha.test:9001/](http://hypha.test:9001/)


## Documentation

To live preview of documentation, while you writing it.

Activate your virtual environment and install dependencies:

```shell
source venv/bin/activate
python3 -m pip install --no-deps -r requirements/dev.txt
```

If utilizing application machine translations, install the required dependencies:

```shell
python3 -m pip install -r requirements/translate.txt
```

Run:
```shell
make serve-docs
```

Open http://localhost:9100/ to preview the documentation site.


!!! tip
    You can use `make serve` command to run Django Development Server, watch and compile frontend changes and preview docs all at once.


## Running tests

Hypha uses `ruff` and [py.test](https://pytest-django.readthedocs.io/en/latest/) test runner and uses `hypha/settings/testing.py` for test settings.
For frontend code, stylelint and eslint is used. 

Run the test with:

```shell
make test
```

For lint the code and not run the full test suite you can use:

```shell
make lint
```

## Helpful URLs

* The Apply dashboard: [http://hypha.test:9001/dashboard/](http://hypha.test:9001/dashboard/)
* The Apply Wagtail admin: [http://hypha.test:9001/admin/](http://hypha.test:9001/admin/)
* The Django Administration panel: [http://hypha.test:9001/django-admin/](http://hypha.test:9001/django-admin/)

Use the email address and password you set in the `createsuperuser` step above to login.

[nvm]: https://github.com/nvm-sh/nvm#readme
[pyenv]: https://github.com/pyenv/pyenv#readme
[Homebrew]: https://brew.sh/
