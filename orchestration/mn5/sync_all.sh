#!/bin/bash
DATACLAY_VERSION=$(cat VERSION)

# Internal MareNostrum paths (do not change!)
MN_TRANSFER_HOST=transfer1.bsc.es
MN_DATACLAY_PATH=/gpfs/apps/MN5/GPP/DATACLAY/$DATACLAY_VERSION
MN_GPP_LUA_PATH=/gpfs/apps/MN5/GPP/modulefiles/applications/dataclay/$DATACLAY_VERSION.lua
MN_ACC_LUA_PATH=/gpfs/apps/MN5/ACC/modulefiles/applications/dataclay/$DATACLAY_VERSION.lua

# bin & config
rsync -av --copy-links bin $MN_TRANSFER_HOST:$MN_DATACLAY_PATH
rsync -av --delete --copy-links config $MN_TRANSFER_HOST:$MN_DATACLAY_PATH

# dataclay src
rsync -av --delete-after --copy-links --filter={":- .gitignore",": /.rsync-filter"} \
	--exclude={.git} ../../ $MN_TRANSFER_HOST:$MN_DATACLAY_PATH/dataclay

# luafile (ACC will use GPP source)
scp modulefile.lua $MN_TRANSFER_HOST:$MN_GPP_LUA_PATH
scp modulefile.lua $MN_TRANSFER_HOST:$MN_ACC_LUA_PATH

# examples
rsync -av --copy-links ../../examples/ $MN_TRANSFER_HOST:~/dc-examples

# storage
mvn -f ../../addons/storage/pom.xml package
rsync -av --delete --exclude target --exclude src ../../addons/storage $MN_TRANSFER_HOST:$MN_DATACLAY_PATH
