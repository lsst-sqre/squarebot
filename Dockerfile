# This Dockerfile has three stages:
#
# base-image
#   Updates the base Python image with security patches and common system
#   packages. This image becomes the base of all other images.
# install-image
#   Installs dependencies and the application into a virtual environment with
#   uv. This virtual environment is ideal for copying across build stages.
# runtime-image
#   - Copies the virtual environment into place.
#   - Runs a non-root user.
#   - Sets up the entrypoint and port.

FROM python:3.14.6-slim-bookworm AS base-image

# Update system packages.
COPY scripts/install-base-packages.sh .
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    ./install-base-packages.sh && rm ./install-base-packages.sh

FROM base-image AS install-image

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /bin/uv

# Install system packages only needed for building dependencies.
COPY scripts/install-dependency-packages.sh .
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    ./install-dependency-packages.sh

# Disable hard links during uv package installation since we're using a
# cache on a separate file system.
ENV UV_LINK_MODE=copy

# Force use of system Python so that the Python version is controlled by
# the Docker base image version, not by whatever uv decides to install.
ENV UV_PYTHON_PREFERENCE=only-system

# Install the dependencies. This repo is a uv workspace, so bind-mount the
# root and client ``pyproject.toml`` (the members the lock references)
# alongside ``uv.lock`` and sync the locked dependencies without installing
# the workspace packages themselves -- those are installed once the source is
# copied in.
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=client/pyproject.toml,target=client/pyproject.toml \
    uv sync --frozen --no-default-groups --compile-bytecode --no-install-workspace

# Install the application itself. ``--no-editable`` materializes the workspace
# packages into the virtual environment so it is self-contained when copied to
# the runtime image.
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --compile-bytecode --no-editable

FROM base-image AS runtime-image

# Create a non-root user.
RUN useradd --create-home appuser

# Copy the virtualenv.
COPY --from=install-image /app/.venv /app/.venv

# Switch to the non-root user.
USER appuser

# Expose the port.
EXPOSE 8080

# Make sure we use the virtualenv.
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

# Run the application.
CMD ["uvicorn", "squarebot.main:app", "--host", "0.0.0.0", "--port", "8080"]
