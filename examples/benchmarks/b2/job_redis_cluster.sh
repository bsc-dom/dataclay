#!/bin/bash -e
#SBATCH --job-name=b2-redis-cluster
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=3
#SBATCH --time=00:30:00
#SBATCH --exclusive
#SBATCH --qos=debug
#############################

# Load dataClay
module load DATACLAY/edge

# Get hostnames
hostnames=($(scontrol show hostname $SLURM_JOB_NODELIST))
hostnames=($(add_network_suffix "-ib0" "${hostnames[@]}"))

# Deploy dataClay
deploy_dataclay \
    --redis ${hostnames[@]::3} \
    --metadata ${hostnames[0]} \
    --backends ${hostnames[@]:1}

# Run client
export DC_HOST=${hostnames[0]}
python3 client.py

# Stop dataClay
cp "job-$SLURM_JOB_ID.out" "$HOME/.dataclay/$SLURM_JOB_ID"
sleep 5