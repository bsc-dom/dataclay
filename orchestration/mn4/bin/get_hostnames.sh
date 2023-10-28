#!/bin/bash

# Get node hostnames with network suffix
network_suffix="-ib0"
hostnames=($(scontrol show hostname $SLURM_JOB_NODELIST | sed "s/$/$network_suffix/"))
echo ${hostnames[@]}