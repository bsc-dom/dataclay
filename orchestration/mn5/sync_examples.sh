#!/bin/bash
MN_TRANSFER_HOST=transfer1.bsc.es

# examples
rsync -av --copy-links ../../examples/ $MN_TRANSFER_HOST:~/dc-examples

