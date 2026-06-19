# Project dev container for Squarebot.
# Based on the Microsoft devcontainers Python image (Debian bookworm),
# matching the Python 3.14 runtime used in production (see ../Dockerfile).
FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

# System packages: build-essential + libffi-dev to build Python dependencies,
# and graphviz to build the Sphinx docs (see ../.github/workflows/ci.yaml).
# git ships in the base image.
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        build-essential \
        libffi-dev \
        graphviz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv, which manages the project's virtual environment and dependency
# groups. `make init` (the devcontainer's postCreateCommand) drives uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
