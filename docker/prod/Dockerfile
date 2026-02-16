#
# Builder stage.
#
FROM python:3.12-bookworm AS builder

# Add venv/bin to PATH.
ENV PATH="/opt/app/.venv/bin:/usr/local/bin:$PATH"

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Set work directory.
WORKDIR /opt/app

# Create the hypha user and group
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g "${APP_GID}" hypha \
  && useradd --create-home --no-log-init -u "${APP_UID}" -g "${APP_GID}" hypha \
  && chown hypha:hypha -R /opt/app

# Set user (default is otherwise root)
USER hypha

# Create directories.
RUN mkdir -p ./hypha/static_compiled && mkdir -p ./media

# Install node.
COPY --from=node:24-slim /usr/local/bin /usr/local/bin
COPY --from=node:24-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin

# Install node dependencies.
COPY --chown=hypha:hypha package*.json ./
RUN npm install --quiet

# Install python dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Copy the project into the image
COPY --chown=hypha:hypha ./ ./

# Build front end.
RUN npm run build && python manage.py collectstatic --noinput --verbosity=0


#
# Production stage.
#
FROM python:3.12-slim-bookworm AS app

# Add venv/bin to PATH.
ENV PATH="/opt/app/.venv/bin:/usr/local/bin:$PATH"

# Set work directory.
WORKDIR /opt/app

# Create the hypha user and group
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g "${APP_GID}" hypha \
  && useradd --create-home --no-log-init -u "${APP_UID}" -g "${APP_GID}" hypha \
  && chown hypha:hypha -R /opt/app

# Set user (default is otherwise root)
USER hypha

# Create directories.
RUN mkdir -p ./hypha/static_compiled && mkdir -p ./media

# Copy venv and assets from builder.
COPY --chown=hypha:hypha --from=builder /opt/app/.venv /opt/app/.venv
COPY --chown=hypha:hypha --from=builder /opt/app/static /opt/app/static

# Copy the project into the image
COPY --chown=hypha:hypha ./ ./

# Run entrypoint.sh.
ENTRYPOINT ["/opt/app/docker/prod/entrypoint.sh"]

# Expose the port gunicorn is running on for other Docker containers.
EXPOSE 8000

CMD ["gunicorn", "--config", "/opt/app/docker/prod/config/gunicorn.py"]
