# Docker

Require most recent version of [Docker](https://www.docker.com/get-started).

## Domains for local development

You will need a domain to run this app.

Add this to your `/etc/hosts` file.

```text
127.0.0.1 hypha.test
```

The "[test](https://en.wikipedia.org/wiki/.test)" TLD is safe to use, it's reserved for testing purposes.

!!! info
    All examples from now on will use the `hypha.test` domains.

## Get the code

```shell
git clone https://github.com/HyphaApp/hypha.git hypha

cd hypha
```

## Create media directory

In production media is stored on AWS S3 but for local development you need a "media" directory.

```shell
mkdir media
```

## Docker

### Build the Docker images

Run the docker compose command to build the images. This will take some time.

If you need to rebuild the images to get a later version just run the "build" again.

```shell
docker compose --file docker/compose.yaml build
```

### Start the docker environment

To start the docker containers you use the "up --watch" command. This command you will use each time you want to start up and use this docker environment.

```shell
docker compose --file docker/compose.yaml  up --watch
```

This will run "npm watch" as well as the "runserver_plus". All code changes to hypha will be synced in to the conatiner thanks to the docker watch functionality.

### Access the docker environment

Go to [http://hypha.test:9001/](http://hypha.test:9001/)

### Stop the docker environment.

Press `ctrl+c` in the terminal window.

### Run commands in the docker environment

To get bash shell on the container that runs the Django app, use this command.

```shell
docker exec -it hypha-django-dev bash
```

Here you can issue django commands as normal.

You can also run commands directly, e.g. "uv sync" like this.

```shell
docker exec hypha-django-dev uv sync
```

To get a shell on the container that runs Postgres, use this command.

```shell
docker exec -i -t hypha-postgres-dev bash
```

## Restore a database dump in Docker

We will use the "public/sandbox\_db.dump" for this example. That is a good start in any case, you get some example content etc.

First copy the sandbox db dump into the container that runs Postgres.

```shell
docker cp public/sandbox_db.dump hypha-postgres-dev:/tmp/
```

Get a shell on the container that runs Postgres.

```shell
docker exec -it hypha-postgres-dev bash
```

Before being able to work on this database, you have to drop and prevent any other connections to it.

```shell
psql --username=hypha -c "REVOKE CONNECT ON DATABASE hypha FROM public;SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'hypha';"
```

With this done, drop and then create the hypha database and run the pg restore command like this.

```shell
dropdb --username=hypha hypha
```

```shell
createdb --username=hypha hypha
```

```shell
pg_restore --verbose --clean --if-exists --no-acl --no-owner --username=hypha --dbname=hypha /tmp/sandbox_db.dump
```

Exit the container shell.

```shell
exit
```

Run the "migrate" and "sync_roles" commands inside the py container to update the db.

```shell
docker exec hypha-django-dev python3 manage.py migrate
```

```shell
docker exec hypha-django-dev python3 manage.py sync_roles
```

Done.
