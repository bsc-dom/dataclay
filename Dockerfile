# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10-bookworm

# install dataclay
FROM python:$PYTHON_VERSION
COPY . /app

RUN python -m pip install --upgrade pip \
  && python -m pip install /app[telemetry]

# prepare dataclay storage dir
RUN mkdir -p /data/storage; 

# set workdir and entrypoint
WORKDIR /workdir
