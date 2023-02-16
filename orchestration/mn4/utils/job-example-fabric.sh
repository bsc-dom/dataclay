#!/bin/bash -e
#SBATCH --job-name=jobexample
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=3
#SBATCH --time=00:03:00
#SBATCH --exclusive 
#SBATCH --qos=debug
#############################

#################
# Configuration # 
#################

# Load Dataclay
module load DATACLAY/DevelMarc

# Get node hostnames with network suffix
network_suffix="-ib0"
hostnames=($(scontrol show hostname $SLURM_JOB_NODELIST | sed "s/$/$network_suffix/"))

# Set environment variables
export DATACLAY_METADATA_HOST=${hostnames[0]} # DO NOT EDIT!
export DC_USERNAME=user
export DC_PASSWORD=s3cret
export DEFAULT_DATASET=myDataset
export STUBS_PATH=./stubs
export MODEL_PATH=./model
export NAMESPACE=dcmodel

export DATACLAY_TRACING=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://${hostnames[0]}:4317 # DO NOT EDIT!
export OTEL_TRACES_SAMPLER=traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1
export OTEL_SERVICE_NAME=client

#######################
# Dataclay deployment #
#######################

echo "Deploying dataClay"
dcdeploy-fabric dataclay -H ${hostnames[@]}

################
# Dataclay app #
################

echo "Starting application"
tracing_prefix=""
if [ $DATACLAY_TRACING == "true" ]; then
    tracing_prefix="opentelemetry-instrument"
fi

$tracing_prefix python3 -u app/matrix-demo.py 1 0

# For testing
# dcdeploy-fabric run "python3 -u app/matrix-demo.py 1 0" -p 3 -H ${hostnames[@]}


#####################
# Stopping dataclay # 
#####################

echo "Stopping dataclay"
dcdeploy-fabric stop -H ${hostnames[@]}
echo "Dataclay stopped"
