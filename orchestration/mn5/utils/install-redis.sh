#!/bin/bash

wget https://download.redis.io/redis-stable.tar.gz
tar -xzvf redis-stable.tar.gz
cd redis-stable
module load gcc/13.2.0
make distclean
make

cp src/redis-server ../bin
cp src/redis-cli ../bin