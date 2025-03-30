#!/bin/bash -e

  export COMPSS_PYTHON_VERSION=3
  module load COMPSs/3.3.1
  module load dataclay

  # Retrieve script arguments
  job_dependency=${1:-None}
  num_nodes=${2:-2}
  execution_time=${3:-5}
  tracing=${4:-false}
  exec_file=${5:-$(pwd)/src/matmul.py}

  # Freeze storage_props into a temporal
  # (allow submission of multiple executions with varying parameters)
  STORAGE_PROPS=`mktemp -p ~`
  cp $(pwd)/storage_props_mn5.cfg "${STORAGE_PROPS}"

  # Define script variables
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  WORK_DIR=${SCRIPT_DIR}/
  APP_CLASSPATH=${SCRIPT_DIR}/src
  APP_PYTHONPATH=${SCRIPT_DIR}/src

  # Define application variables
  graph=$tracing
  log_level="off"
  qos_flag="--qos=gp_debug"
  workers_flag=""
  constraints="highmem"

  # Create workers sandbox
  # mkdir -p "${WORK_DIR}/COMPSs_Sandbox"
  # --job_execution_dir="${WORK_DIR}" \
  # --worker_working_dir="${WORK_DIR}/COMPSs_Sandbox" \

  CPUS_PER_NODE=112
  WORKER_IN_MASTER=100

  if [ "$#" -gt 4 ]; then shift 5; fi

  # Those are evaluated at submit time, not at start time...
  COMPSS_VERSION=`ml whatis COMPSs 2>&1 >/dev/null | awk '{print $1 ; exit}'`
  DATACLAY_VERSION=`ml whatis DATACLAY 2>&1 >/dev/null | awk '{print $1 ; exit}'`

  # This path will also be inherited by the dataClay backend
  export PYTHONPATH=$PYTHONPATH:$APP_PYTHONPATH

  # Enqueue job
  enqueue_compss \
    --project_name="bsc19" \
    --job_name=matmulOO_PyCOMPSs_dataClay \
    --job_dependency="${job_dependency}" \
    --exec_time="${execution_time}" \
    --num_nodes="${num_nodes}" \
    \
    --cpus_per_node="${CPUS_PER_NODE}" \
    --worker_in_master_cpus="${WORKER_IN_MASTER}" \
    \
    "${workers_flag}" \
    \
    --worker_working_dir=$(pwd) \
    \
    --constraints=${constraints} \
    --tracing="${tracing}" \
    --graph="${graph}" \
    --summary \
    --log_level="${log_level}" \
    "${qos_flag}" \
    \
    --classpath=$DATACLAY_HOME/storage/StorageItf-1.0.jar \
    --pythonpath=${PYCLAY_PATH}:${PYTHONPATH} \
    --storage_props=${STORAGE_PROPS} \
    --storage_home=$DATACLAY_HOME/storage \
    \
    ${extra_tracing_flags} \
    \
    --lang=python \
    \
    "$exec_file" $@ --use_storage

# Enqueue tests example:
# ./launch_with_dataClay.sh None 2 5 false $(pwd)/src/matmul.py -b 4 -e 4 --check_result
# ./launch_with_dataClay.sh None 2 60 true $(pwd)/src/matmul.py -b 16 -e 4096

# OUTPUTS:
# - compss-XX.out : Job output file
# - compss-XX.err : Job error file
# - ~/.COMPSs/JOB_ID/ : COMPSs files
