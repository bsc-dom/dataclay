#!/bin/bash


runcompss \
  -g \
  --pythonpath=/root/examples/wordcount/src \
  --storage_impl=dataclay \
  --storage_conf=/root/examples/wordcount/storage_props.cfg \
  /root/examples/wordcount/src/wordcount.py -d /root/examples/wordcount/dataset/ --use_storage
