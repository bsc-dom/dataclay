# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10-bookworm

# install dataclay
FROM python:$PYTHON_VERSION
COPY . /app

ARG LEGACY_DEPS=False
RUN python -m pip install --upgrade pip \
  && python -m pip install --config-settings=LEGACY_DEPS=$LEGACY_DEPS /app[telemetry]

# prepare dataclay storage dir
RUN mkdir -p /data/storage; 

# set workdir and entrypoint
WORKDIR /workdir
