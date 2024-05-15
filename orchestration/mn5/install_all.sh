#!/bin/bash
DATACLAY_VERSION=$(cat VERSION)
# Internal MareNostrum paths (do not change!)
# It is necessary a VPN connection in order to use MN_INTERNET_HOST login (the only login with internet)
MN_INTERNET_HOST=glogin4.bsc.es
MN_DATACLAY_PATH=/apps/GPP/DATACLAY/$DATACLAY_VERSION


# install dataClay in a Python virtual environment
ssh $MN_INTERNET_HOST "cd $MN_DATACLAY_PATH && bash -s" -- 3.12 <utils/install-venv-dataclay.sh

# install Redis
ssh $MN_INTERNET_HOST "cd $MN_DATACLAY_PATH && bash -s" -- <utils/install-redis.sh

# install otelcol
ssh $MN_INTERNET_HOST "cd $MN_DATACLAY_PATH && bash -s" -- <utils/install-otelcol.sh
