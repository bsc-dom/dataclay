#!/bin/bash
DATACLAY_VERSION=$(cat VERSION)

# Internal MareNostrum paths (do not change!)
MN1_HOST=mn1.bsc.es
MN_DATACLAY_PATH=/apps/DATACLAY/$DATACLAY_VERSION/
MN_LUA_PATH=/apps/modules/modulefiles/tools/DATACLAY/$DATACLAY_VERSION.lua

# bin & config
rsync -av --copy-links bin $MN1_HOST:$MN_DATACLAY_PATH
rsync -av --delete --copy-links config $MN1_HOST:$MN_DATACLAY_PATH

# dataclay src
rsync -av --delete-after --copy-links --filter={":- .gitignore",": /.rsync-filter"} \
	--exclude={.git} ../../ $MN1_HOST:$MN_DATACLAY_PATH/dataclay

# luafile
scp modulefile.lua $MN1_HOST:$MN_LUA_PATH

# examples
rsync -av --delete --copy-links ../../examples $MN1_HOST:~/

# storage
mvn -f ../../addons/storage/pom.xml package
rsync -av --delete --exclude target --exclude src ../../addons/storage $MN1_HOST:$MN_DATACLAY_PATH
