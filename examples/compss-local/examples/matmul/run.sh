#!/bin/bash

runcompss \
  -g \
  --log_level=off \
  --pythonpath=/root/examples/matmul/src \
  --summary \
  /root/examples/matmul/src/matmul.py -b 4 -e 4 --check_result
