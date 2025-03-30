#!/bin/bash


runcompss \
  -d \
  --pythonpath=/root/examples/kmeans/src \
  --storage_impl=dataclay \
  --storage_conf=/root/examples/kmeans/storage_props.cfg \
  /root/examples/kmeans/src/kmeans.py -n 1024 -f 8 -d 2 -c 4 --use_storage
