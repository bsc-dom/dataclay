#!/bin/bash -e
#SBATCH --job-name=tracing
#SBATCH --output=job-%A.out
#SBATCH --error=job-%A.out
#SBATCH --nodes=2
#SBATCH --time=00:05:00
#SBATCH --exclusive
#SBATCH --qos=debug
#############################

# Load dataClay
module load DATACLAY/edge

# Deploy dataClay and run client
dataclay_job_v1 client.py

