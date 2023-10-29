#!/bin/bash -e
#SBATCH --job-name=example
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=2
#SBATCH --time=00:05:00
#SBATCH --exclusive
#SBATCH --qos=debug
#############################

# Load dataclay
module load DATACLAY/edge

hostnames=($(scontrol show hostname $SLURM_JOB_NODELIST))

deploy_dataclay \
    --redis ${hostnames[0]} \
    --metadata ${hostnames[0]} \
    --backends ${hostnames[@]:1}

# Run script
export DC_HOST=${hostnames[0]}
python3 client.py

# Shutdown
cp "job-$SLURM_JOB_ID.out" "$HOME/.dataclay/$SLURM_JOB_ID"
sleep 5
