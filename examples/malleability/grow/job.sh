#!/bin/bash -e
#SBATCH --job-name=malleability
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=3
#SBATCH --time=00:10:00
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
    --redis ${hostnames[0]} \
    --metadata ${hostnames[0]} \
    --backends ${hostnames[1]}

# Run client
export DC_HOST=${hostnames[0]} # Need by client.py and ctl.stop_dataclay
python3 client.py

# Deploy new backend
export DATACLAY_KV_HOST=${hostnames[0]} # Need by new backend deployment
deploy_dataclay \
    --backends ${hostnames[2]}

# Run client again
python3 client.py

# Stop dataClay
python3 -m dataclay.control.ctl stop_dataclay
cp "job-$SLURM_JOB_ID.out" "$HOME/.dataclay/$SLURM_JOB_ID"
