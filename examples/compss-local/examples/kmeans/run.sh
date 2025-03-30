#!/bin/bash


export NO_STORAGE=true

runcompss \
  -g \
  --env_script=/root/examples/kmeans/env_vars.sh \
  --pythonpath=/root/examples/kmeans/src \
  /root/examples/kmeans/src/kmeans.py -n 1024 -f 8 -d 2 -c 4
