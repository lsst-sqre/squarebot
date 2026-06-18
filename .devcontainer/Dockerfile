# Project dev container for Squarebot.
# Based on the Microsoft devcontainers Python image (Debian bookworm),
# matching the Python 3.12 runtime used in production (see ../Dockerfile).
FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# System packages: build-essential + libffi-dev to build Python dependencies
# (see ../scripts/install-dependency-packages.sh), and graphviz to build the
# Sphinx docs (see ../.github/workflows/ci.yaml). git ships in the base image.
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        build-essential \
        libffi-dev \
        graphviz \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
