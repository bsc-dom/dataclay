ARG DATACLAY_VERSION=latest

FROM ghcr.io/bsc-dom/dataclay:$DATACLAY_VERSION

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt