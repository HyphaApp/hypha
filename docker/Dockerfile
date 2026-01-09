FROM python:3.12-bookworm

# Add venv/bin to PATH.
ENV PATH="/opt/app/.venv/bin:/usr/local/bin:$PATH"

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Set work directory.
WORKDIR /opt/app

# Install node.
COPY --from=node:24-slim /usr/local/bin /usr/local/bin
COPY --from=node:24-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin

# Install node dependencies.
COPY package*.json ./
RUN npm install --quiet

# Install python dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync

# Copy the project into the image
COPY ./ ./

# Create directories.
RUN mkdir -p ./hypha/static_compiled && mkdir -p ./hypha/media

# Build front end.
RUN npm run dev:build

# Run entrypoint.sh.
ENTRYPOINT ["/opt/app/docker/entrypoint.sh"]
