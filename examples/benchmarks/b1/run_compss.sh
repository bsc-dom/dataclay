module load COMPSs/3.3
module load hdf5 python/3.12 dataclay/edge

enqueue_compss \
	--storage_home=$DATACLAY_HOME/storage/ \
	--storage_props=.env \
	--classpath=$DATACLAY_HOME/storage/StorageItf-1.0.jar \
	--pythonpath=$DATACLAY_PYTHONPATH:$PWD \
	--project_name="bsc19" \
	--qos=gp_debug \
	--num_nodes=3 \
	client_compss.py
