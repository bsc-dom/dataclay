#!/bin/bash -e
#SBATCH --job-name=fabrictest
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=3
#SBATCH --time=00:05:00
#SBATCH --exclusive 
#SBATCH --qos=debug
#############################

# Load dataclay
module load DATACLAY/DevelMarc

# Get node hostnames with network suffix
network_suffix="-ib0"
hostnames=($(scontrol show hostname $SLURM_JOB_NODELIST | sed "s/$/$network_suffix/"))

# Create hosts file
hosts_file=hosts-$SLURM_JOB_ID
echo "[metadata]" > $hosts_file
echo ${hostnames[0]} >> $hosts_file
echo "[backends]" >> $hosts_file 
printf "%s\n" ${hostnames[@]:1} >> $hosts_file

# Set dataclay configuration
export DATACLAY_METADATA_HOSTNAME=${hostnames[0]} # DO NOT EDIT!
export KV_HOST=${hostnames[0]} # DO NOT EDIT!
export DATACLAY_LOGLEVEL=DEBUG

# Set tracing configuration
export DATACLAY_TRACING=false
export OTEL_EXPORTER_OTLP_ENDPOINT=http://${hostnames[0]}:4317 # DO NOT EDIT!
export OTEL_TRACES_SAMPLER=traceidratio
export OTEL_TRACES_SAMPLER_ARG=0.1
export OTEL_SERVICE_NAME=client

# Set admin credentials
export DATACLAY_USERNAME=testuser
export DATACLAY_PASSWORD=s3cret
export DATACLAY_DATASET=testuser

# Set client credentials
export DC_USERNAME=testuser
export DC_PASSWORD=s3cret
export DC_DATASET=testuser

# Deploy dataclay
dataclay-deploy -i $hosts_file

# Run script
python3 matrix-generator.py --matrices 5 --size 100 --path ./data/
python3 script.py 10 0 --processes 1 --path $PWD/data/
sleep 10

# Shutdown
cp job-$SLURM_JOB_ID.out $HOME/.dataclay/$SLURM_JOB_ID