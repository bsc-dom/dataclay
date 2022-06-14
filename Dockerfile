# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10-bullseye

FROM python:$PYTHON_VERSION

# set a work directory and copy pyclay
WORKDIR /pyclay
COPY . .

# install pyclay and its dependencies
RUN python -m pip install --upgrade pip \
    && python -m pip install .

# prepare dataclay storage dir
RUN mkdir -p /dataclay/storage; \
    mkdir -p /dataclay/metadata

# set entrypoint
ENTRYPOINT ["python", "-m", "dataclay.executionenv.server"]
