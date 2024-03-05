#!/bin/bash

#############################################################
# Name: storage_init.sh
# Description: Storage API script for COMPSs
# Parameters: 
#   1) job_id              	- Queue Job Id
#   2) master_node         	- COMPSs Master Node
#   3) storage_master_node	- Node reserved for Storage Master Node (if different)
#   4) worker_nodes        	- Nodes set as COMPSs workers (quoted)
#   5) network            	- Network type
#   6) storage_props       	- Properties file for storage specific variables
#############################################################


# Constants
readonly NUM_PARAMS=6

# Function to display usage information
usage() {
    local exit_value="${1:-1}"
    echo "Usage: $0 <job_id> <master_node> <storage_master_node> \"<worker_nodes>\" <network> <storage_props>"
    echo
    exit "$exit_value"
}

# Function to parse and validate script arguments
get_args() {
    if [ "$#" -lt $NUM_PARAMS ] || [ "$1" == "usage" ]; then
        echo "Error: Invalid number of arguments."
        usage
    fi

    # Assign parameters to readable variables
    job_id="$1"
    master_node="$2"
    storage_master_node="$3"
    IFS=' ' read -r -a worker_nodes <<< "$4"
    network="$5"
    storage_props="$6"
    # variables_to_be_sourced="$7"
    # storage_container_image="$8"
    # storage_cpu_affinity="$9"

    # Validate required parameters
    if [ -z "$job_id" ] || [ -z "$master_node" ] || [ -z "$network" ] || [ -z "$storage_props" ]; then
        echo "Error: Missing required arguments."
        usage
    fi

    # Validate file existence
	if [ ! -f "$storage_props" ]; then
        echo "Error: File '$storage_props' not found."
        exit 2
    fi
}

# Function to configure COMPSs specific settings
configure_compss() {
    local session_config_dir="$HOME/.COMPSs/${job_id}/storage/cfgfiles"
    mkdir -p "$session_config_dir"

    # Copy and append information to the storage properties file
    local storage_properties_file="$session_config_dir/storage.properties"
    cp "$storage_props" "$storage_properties_file"

    # Add DC_HOST to the properties file
    echo "" >> "$storage_properties_file"
    echo "DC_HOST=$master_node" >> "$storage_properties_file"
}

# Main function to orchestrate the script execution
main() {
    get_args "$@"

    master_node=($(add_network_suffix "$network" "${master_node[@]}"))
    worker_nodes=($(add_network_suffix "$network" "${worker_nodes[@]}"))

    deploy_dataclay \
        --redis "$master_node" \
        --metadata "$master_node" \
        --backends "${worker_nodes[@]}" \
        --env-file "$storage_props"

    configure_compss
}

# Script execution starts here
main "$@"