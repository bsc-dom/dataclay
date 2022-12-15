# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10-bullseye

# install pyclay
FROM python:$PYTHON_VERSION
COPY . /pyclay
RUN python -m pip install --upgrade pip \
    && python -m pip install /pyclay

# prepare dataclay storage dir
RUN mkdir -p /dataclay/storage; \
    mkdir -p /dataclay/metadata

# set workdir and entrypoint
WORKDIR /workdir
CMD echo "MAMA"