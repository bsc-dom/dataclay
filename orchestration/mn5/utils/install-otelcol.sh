#!/bin/bash

# Downloads otelcol-contrib binary and save it to ./bin
# Modified script from https://github.com/etcd-io/etcd/releases/

OTELCOL_VER=0.100.0

# choose either URL
GITHUB_URL=https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download
DOWNLOAD_URL=${GITHUB_URL}

# otelcol
curl -L ${DOWNLOAD_URL}/v$OTELCOL_VER/otelcol_${OTELCOL_VER}_linux_amd64.tar.gz -o ./bin/otelcol_${OTELCOL_VER}_linux_amd64.tar.gz
tar xzvf ./bin/otelcol_${OTELCOL_VER}_linux_amd64.tar.gz -C ./bin/ otelcol
rm -f ./bin/otelcol_${OTELCOL_VER}_linux_amd64.tar.gz

# otelcol-contrib
curl -L ${DOWNLOAD_URL}/v$OTELCOL_VER/otelcol-contrib_${OTELCOL_VER}_linux_amd64.tar.gz -o ./bin/otelcol-contrib_${OTELCOL_VER}_linux_amd64.tar.gz
tar xzvf ./bin/otelcol-contrib_${OTELCOL_VER}_linux_amd64.tar.gz -C ./bin/ otelcol-contrib
rm -f ./bin/otelcol-contrib_${OTELCOL_VER}_linux_amd64.tar.gz
