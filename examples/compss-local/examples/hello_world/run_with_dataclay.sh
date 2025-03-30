#!/bin/bash


runcompss \
  -g \
  --log_level=off \
  --storage_impl=dataclay \
  --storage_conf=/root/examples/hello_world/storage_props.cfg \
  /root/examples/hello_world/src/hello_world.py --use_storage
