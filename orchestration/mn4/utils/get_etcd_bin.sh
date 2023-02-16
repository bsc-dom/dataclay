#!/bin/bash

# Downloads etcd binaries and save them to ./bin
# Modified script from https://github.com/etcd-io/etcd/releases/

ETCD_VER=v3.5.5

# choose either URL
GOOGLE_URL=https://storage.googleapis.com/etcd
GITHUB_URL=https://github.com/etcd-io/etcd/releases/download
DOWNLOAD_URL=${GOOGLE_URL}

curl -L ${DOWNLOAD_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz -o ./bin/etcd-${ETCD_VER}-linux-amd64.tar.gz
tar xzvf ./bin/etcd-${ETCD_VER}-linux-amd64.tar.gz -C ./bin/ --wildcards '*/etcd*' --strip-components=1

rm -f ./bin/etcd-${ETCD_VER}-linux-amd64.tar.gz