FROM python:3.12.7-bookworm

# Add venv/bin to PATH.
ENV PATH="/opt/app/.venv/bin:/usr/local/bin:$PATH"

# Set work directory.
WORKDIR /opt/app

# Install node.
COPY --from=node:20.18-slim /usr/local/bin /usr/local/bin
COPY --from=node:20.18-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /usr/local/bin

# Install node dependencies.
COPY package*.json ./
RUN npm install --quiet

# Install python dependencies.
COPY pyproject.toml uv.lock ./
RUN uv sync

# Copy the project into the image
COPY ../.. ./

# Create directories.
RUN mkdir -p ./hypha/static_compiled && mkdir -p ./hypha/media

# Build front end.
RUN npm run dev:build

# Run entrypoint.sh.
ENTRYPOINT ["/opt/app/docker/dev/entrypoint.sh"]
