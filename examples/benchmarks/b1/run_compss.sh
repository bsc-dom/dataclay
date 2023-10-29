module load COMPSs/3.2
module load DATACLAY/marc.dev

enqueue_compss \
	--storage_home=$DATACLAY_HOME/storage/ \
	--storage_props=.env \
	--classpath=$DATACLAY_HOME/storage/StorageItf-1.0.jar \
	--pythonpath=$DATACLAY_PYTHONPATH:$PWD \
	--qos=debug \
	--num_nodes=3 \
	client_compss.py
