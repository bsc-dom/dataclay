#!/bin/bash

wget https://download.redis.io/redis-stable.tar.gz
tar -xzvf redis-stable.tar.gz
cd redis-stable
module load gcc/12.1.0_binutils
make distclean
make

cp src/redis-server ../bin
cp src/redis-cli ../bin