#!/bin/bash -e
#SBATCH --job-name=b1
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=2
#SBATCH --time=00:05:00
#SBATCH --exclusive
#SBATCH --qos=gp_debug
#############################

# Load dataClay
module load hdf5 python/3.12 dataclay/edge

# Deploy dataClay and run client
dataclay_job_v1 client.py