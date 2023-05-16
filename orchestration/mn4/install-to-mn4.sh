#!/bin/bash
source config.sh

# Internal MareNostrum paths (do not change!)
# It is necessary a VPN connection in order to use MN0 login (the only login with internet)
MN0_HOST=$BSC_USER@mn0.bsc.es
MN_DATACLAY_PATH=/apps/DATACLAY/$DATACLAY_VERSION/

# install dataClay in a Python virtual environment
ssh $MN0_HOST "cd $MN_DATACLAY_PATH && bash -s" -- < utils/install-venv-dataclay.sh 3.10.2

# install Redis
ssh $MN0_HOST "cd $MN_DATACLAY_PATH && bash -s" -- < utils/install-redis.sh