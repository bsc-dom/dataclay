#!/bin/bash
#############################################################
# Name: storage_init.sh
# Description: Storage API script for COMPSs
# Parameters: <jobId>              Queue Job Id
#             <masterNode>         COMPSs Master Node
#             <storageMasterNode>  Node reserved for Storage Master Node (if needed)
#             "<workerNodes>"      Nodes set as COMPSs workers
#             <network>            Network type
#             <storageProps>       Properties file for storage specific variables
#############################################################

#=== FUNCTION ================================================================
# NAME: usage
# DESCRIPTION: Display usage information for this script.
# PARAMETER 1: exit value
#=============================================================================
usage() {
    local exitValue=$1
    echo " Usage: $0 <jobId> <masterNode> <storageMasterNode> \"<workerNodes>\" <network> <storageProps>"
    echo " "
    exit $exitValue
}

#=== FUNCTION ================================================================
# NAME: usage
# DESCRIPTION: Display usage information for this script.
# PARAMETER 1: ---
#=============================================================================
get_args() {
	NUM_PARAMS=6
	# Check parameters
	if [ $# -eq 1 ]; then
		if [ "$1" == "usage" ]; then
			usage 0
		fi
	fi
	# Get parameters
	jobId=$1
	master_node=$2
	storage_master_node=$3
	# worker_nodes=$4
    read -r -a worker_nodes <<< $4
	network=$5
	storageProps=$6
}
# -------------- 


get_args "$@"

# Load dataclay
module load DATACLAY/DevelMarc


network_suffix=""
if [ "${network}" == "infiniband" ]; then
	network_suffix="-ib0"
fi

# Save hosts inventory
hosts_file=hosts-$SLURM_JOB_ID
# . dc-hosts-1 >"$hosts_file"

# COMPSS_HOSTS="$storage_master_node $storage_master_node $worker_nodes"
# JOB_HOSTS=($(echo $COMPSS_HOSTS | tr " " "\n"))
# HOSTS=""
# # Get hosts and add infiniband suffix if needed
# for HOST in ${JOB_HOSTS[@]}; do
#         HOSTS="$HOSTS ${HOST}${NETWORK_SUFFIX}"
# done

echo "[metadata]" > $hosts_file
echo "$master_node""$network_suffix" >> $hosts_file
echo "[backends]" >> $hosts_file
printf "%s$network_suffix\n" "${worker_nodes[@]}" >> $hosts_file

export DATACLAY_METADATA_HOST=$master_node
export DATACLAY_KV_HOST=$master_node


# Export envs
if [ ! -f ${storageProps} ]; then
	# PropsFile doesn't exist
	echo "ERROR: storage properties file ${storageProps} does not exist" 
	exit 1
fi
set -a
source $storageProps
set +a

# Deploy dataclay
ansible-playbook "$DATACLAY_HOME/config/deploy-playbook.yaml" -i "$hosts_file"


#-------------------------------------- COMPSs specifc -------------------------------------------------
# Get session config
mkdir -p ~/.COMPSs/${SLURM_JOB_ID}/storage/cfgfiles
cp $storageProps ~/.COMPSs/${SLURM_JOB_ID}/storage/cfgfiles/storage.properties
echo "DC_HOST=$DATACLAY_METADATA_HOST" >> ~/.COMPSs/${SLURM_JOB_ID}/storage/cfgfiles/storage.properties


