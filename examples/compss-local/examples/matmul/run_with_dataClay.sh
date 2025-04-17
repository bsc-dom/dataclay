#!/bin/bash


runcompss \
  -g \
  --pythonpath=/root/examples/matmul/src \
  --storage_impl=dataclay \
  --storage_conf=/root/examples/matmul/storage_props.cfg \
  --summary \
  /root/examples/matmul/src/matmul.py -b 4 -e 4 --check_result --use_storage
