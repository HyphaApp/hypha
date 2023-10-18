# Docker

This is a set of instructions on spinning up hypha in a docker container for
evaluation of the system. While Docker is a well suited to this type of quick
exploration, we do not currently recommend these docker instructions for
production use. Instead, we advise production deployments to instead install
into a [stand-alone](stand-alone.md) directory.

## Requirements

Recent version of [Docker](https://www.docker.com/get-started).

## Domains

You will need two domain to run this app. One for the public site and one for the apply site. Make sure your DNS points to the server running these containers.

## Get the code

```text
git clone https://github.com/HyphaApp/hypha.git hypha

cd hypha
```

Everything from now on will happen inside the hypha directory.

## Docker

### Modify Docker and Nginx Files

There are several files you will need to modify before you run docker-compose.

* docker-compose: 
  * change line `dockerfile: docker/Dockerfile.dev` to read `dockerfile: docker/Dockerfile.prod`
  * change ports in web section to '80:80'
* Dockerfile.prod: in Environment variables section: add your domain.
* Move `nginx/hypha.conf` to `nginx/hypha-dev.conf` and move `nginx/hypha-prod.conf` to `nginx/hypha.conf`

  **Build the Docker images**

Move to the "docker" directory.

```text
cd docker
```

Run the docker compose command to build the images. This will take some time.

If you need to rebuild the images to get a later version just run the "build" again.

```text
docker-compose build
```

### Start the docker environment

To start the docker containers you use the "up" command. This command you will use each time you want to start up and use this docker environment.

```text
docker-compose up
```

### Access the docker environment

Go to your domain - you should see the app deployed.

### Run commands in  the docker environment

To get bash shell on the container that runs the Django app, use this command.

```text
docker-compose exec py bash
```

Here you can issue django commands as normal. You might want to change the user - the default is circleci, but most of the code is owned by the user 'node'. To do that:

`docker-compose exec -u node py bash`

To get a shell on the container that runs Postgres, use this command.

```text
docker-compose exec db bash
```

### Stop the docker environment.

Press ++ctrl+c++ in the terminal window.

## Other considerations

### Setting your own PostgreSQL password

In the docker-compose.yml file, there is under db, an environment section with database name, user, and password. You can set those, then remember, in the Docker file, to use those in the DATABASE\_URL environment variable.

### SSL certificates

This setup is port 80 only. To set up an SSL certificate, you'd have to:

* add port 443 to the nginx section of the docker-compose file
* add a volume to hold your certs
* add the certification info to the nginx configuration file

