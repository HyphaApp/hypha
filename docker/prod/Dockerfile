#
# Builder stage.
#
FROM python:3.12.7-bookworm AS builder

# Add venv/bin to PATH.
ENV PATH="/opt/app/.venv/bin:/usr/local/bin:$PATH"

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Set work directory.
WORKDIR /opt/app

# Create directories.
RUN mkdir -p ./hypha/static_compiled && mkdir -p ./hypha/media

# Install node.
COPY --from=node:20.18-slim /usr/local/bin /usr/local/bin
COPY --from=node:20.18-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin

# Install node dependencies.
COPY package*.json ./
RUN npm install --quiet

# Install python dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Copy the project into the image
COPY ./ ./

# Build front end.
RUN npm run build && python manage.py collectstatic --noinput --verbosity=0


#
# Production stage.
#
FROM python:3.12.7-slim-bookworm

# Add venv/bin to PATH.
ENV PATH="/opt/app/.venv/bin:/usr/local/bin:$PATH"

# Set work directory.
WORKDIR /opt/app

# Create directories.
RUN mkdir -p ./hypha/static_compiled && mkdir -p ./hypha/media

# Copy venv and assets from builder.
COPY --from=builder /opt/app/.venv /opt/app/.venv
COPY --from=builder /opt/app/static /opt/app/static

# Copy the project into the image
COPY ./ ./

# Run entrypoint.sh.
ENTRYPOINT ["/opt/app/docker/prod/entrypoint.sh"]
