#!/bin/bash

runcompss \
  -g \
  --log_level=off \
  /root/examples/wordcount/src/wordcount.py -d /root/examples/wordcount/dataset/
