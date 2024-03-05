#!/bin/bash -e
#SBATCH --job-name=fabrictest
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=3
#SBATCH --time=00:05:00
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
    --backends ${hostnames[@]:1}

# Run client
export DC_HOST=${hostnames[0]}
python3 matrix-generator.py --matrices 5 --size 100 --path ./data/
# python3 client.py 10 0 --processes 1 --path $PWD/data/

# Testing multiple clients
# set --forks to the number of clients
ansible-playbook "$DATACLAY_HOME/config/run-playbook.yaml" \
	-i "$hosts_file" -f 3 \
	-e "script='python3 client.py 10 0 --processes 1 --path $PWD/data/'"

# Stop dataClay
cp "job-$SLURM_JOB_ID.out" "$HOME/.dataclay/$SLURM_JOB_ID"
sleep 5


