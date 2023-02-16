#!/bin/bash

# Script to sync dataclay and orchestration files to MareNostrum4
# Change the necessary fields!

##############
# TO CHANGE! #
##############

DATACLAY_VERSION=DevelMarc
BSC_USER=bsc25877
PYCLAY_PATH=~/dev/bsc-dom/pyclay

##############

# Internal MareNostrum paths (do not change!)
MN1_HOST=$BSC_USER@mn1.bsc.es
MN0_HOST=$BSC_USER@mn0.bsc.es
MN_DATACLAY_PATH=/apps/DATACLAY/$DATACLAY_VERSION/
MN_LUA_PATH=/apps/modules/modulefiles/tools/DATACLAY/$DATACLAY_VERSION.lua

# bin & config
rsync -av --copy-links bin $MN1_HOST:$MN_DATACLAY_PATH
rsync -av --delete --copy-links config $MN1_HOST:$MN_DATACLAY_PATH

# pyclay
rsync -av --delete-after --copy-links --filter={":- .gitignore",": /.rsync-filter"} --exclude={.git} $PYCLAY_PATH $MN1_HOST:$MN_DATACLAY_PATH

# lua
scp modulefile.lua $MN1_HOST:$MN_LUA_PATH

# Comment the next line if not wanting to create the virtual environments.
# It is necessary a VPN connection in order to use MN0 login (the only login with internet)
# ssh $MN0_HOST "cd $MN_DATACLAY_PATH && bash -s" -- < utils/install_pyclay.sh 3.10.2
