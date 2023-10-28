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
module load DATACLAY/marc.dev

hostnames=($(scontrol show hostname $SLURM_JOB_NODELIST))

deploy_dataclay \
    --redis ${hostnames[0]} \
    --metadata ${hostnames[0]} \
    --backends ${hostnames[@]:1}

# Run script
export DC_HOST=${hostnames[0]}
python3 client.py

sleep 5

# Shutdown
cp "job-$SLURM_JOB_ID.out" "$HOME/.dataclay/$SLURM_JOB_ID"
