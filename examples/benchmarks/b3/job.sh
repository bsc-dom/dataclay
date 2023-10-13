#!/bin/bash -e
#SBATCH --job-name=hello-family
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=2
#SBATCH --time=00:05:00
#SBATCH --exclusive
#SBATCH --qos=debug
#############################

# Load dataclay
module load DATACLAY/edge

# Save hosts inventory
hosts_file=hosts-$SLURM_JOB_ID
. dc-hosts-1 >"$hosts_file"

# Set dataclay configuration
export DATACLAY_LOGLEVEL=DEBUG

# Set tracing configuration
# export DATACLAY_TRACING=false
# export OTEL_EXPORTER_OTLP_ENDPOINT=http://${hostnames[0]}:4317 # DO NOT EDIT!
# export OTEL_TRACES_SAMPLER=traceidratio
# export OTEL_TRACES_SAMPLER_ARG=0.1
# export OTEL_SERVICE_NAME=client

# Set admin credentials
export DATACLAY_USERNAME=testuser
export DATACLAY_PASSWORD=s3cret
export DATACLAY_DATASET=testdata

# Set client credentials
export DC_USERNAME=testuser
export DC_PASSWORD=s3cret
export DC_DATASET=testdata

# Deploy dataclay
ansible-playbook "$DATACLAY_HOME/config/deploy-playbook.yaml" -i "$hosts_file"

# Run script
python3 client.py

sleep 5

# Shutdown
cp "job-$SLURM_JOB_ID.out" "$HOME/.dataclay/$SLURM_JOB_ID"