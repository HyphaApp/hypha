# With Docker

Require most recent version of [Docker](https://www.docker.com/get-started).

## Domains for local development

You will need two domain to run this app. One for the public site and one for the apply site.

Add this to your `/etc/hosts` file.

```text
127.0.0.1 hypha.test
127.0.0.1 apply.hypha.test
```

The "[test](https://en.wikipedia.org/wiki/.test)" TLD is safe to use, it's reserved for testing purposes.

OBS! All examples from now on will use the `hypha.test` domains.

## Get the code

```console
git clone https://github.com/HyphaApp/hypha.git hypha

cd hypha
```

## Create media directory

In production media is stored on AWS S3 but for local development you need a "media" directory.

```console
mkdir media
```

## Docker

### Build the Docker images

Run the docker compose command to build the images. This will take some time.

If you need to rebuild the images to get a later version just run the "build" again.

```console
docker-compose --file docker/docker-compose.yaml build
```

The build command needs to be run from Hypha root so it can copy needed files. The other commands are easier to run directly from the "docker" sub directory.

### Start the docker environment

Move to the "docker" directory.

```console
cd docker
```

To start the docker containers you use the "up" command. This command you will use each time you want to start up and use this docker environment.

```console
docker-compose up
```

### Access the docker environment

Go to [http://hypha.test:8090/](http://hypha.test:8090/)

### Run commands in the docker environment

To get bash shell on the container that runs the Django app, use this command.

```console
docker-compose exec py bash
```

Here you can issue django commands as normal. You might want to change the user - the default is circleci, but most of the code is owned by the user 'node'. To do that:

```console
docker-compose exec -u node py bash
```

To get a shell on the container that runs Postgres, use this command.

```console
docker-compose exec db bash
```

### Stop the docker environment.

Press `ctrl+c` in the terminal window.

## Restore a database dump in Docker

We will use the "public/sandbox\_db.dump" for this example. That is a good start in any case, you get some example content etc.

First get a shell on the db container.

```console
docker-compose exec db bash
```

Then in that shell you need to install `wget` to download the db dump.

```console
apt update
apt install wget
```

Then download the sandbox db dump from Github.

```console
wget https://github.com/HyphaApp/hypha/raw/sandbox/public/sandbox_db.dump
```

Before being able to work on this database, you have to drop and prevent any other connections to it.

```console
psql
```

```sql
REVOKE CONNECT ON DATABASE hypha FROM public;
SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'hypha';
```

With this done, drop and then create the hypha database and run the pg restore command like this.

```console
dropdb --user=hypha hypha
createdb --user=hypha hypha
pg_restore --verbose --clean --if-exists --no-acl --no-owner --dbname=hypha --username=hypha sandbox_db.dump
```

After restoring the sandbox db run the migrate command inside the py container.

```console
docker-compose exec py bash
python3 manage.py migrate
```
