#!/bin/bash
MN1_HOST=mn1.bsc.es

# examples
rsync -av --delete --copy-links ../../examples $MN1_HOST:~/

