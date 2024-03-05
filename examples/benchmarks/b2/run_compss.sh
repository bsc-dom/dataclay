module load COMPSs/3.2
module load DATACLAY/edge

enqueue_compss \
	--storage_home=$DATACLAY_HOME/storage/ \
	--storage_props=$DATACLAY_HOME/storage/storage_props_example \
	--classpath=$DATACLAY_HOME/storage/StorageItf-1.0.jar \
	--pythonpath=$DATACLAY_PYTHONPATH:$PWD \
	--qos=debug \
	--num_nodes=4 \
	--exec_time=30 \
	--worker_working_dir=local_disk \
	--scheduler=es.bsc.compss.scheduler.orderstrict.fifo.FifoTS \
	client_compss.py
