#!/bin/bash

set -e

# Load python module
python_version="${1:-3.12}"
module load mkl intel hdf5 "python/$python_version"

# Define paths
lib_path="./lib/python$python_version"
packages_path="$lib_path/site-packages"
bin_path="$lib_path/bin"

# Remove previous installations
rm -rf $lib_path
mkdir -p $packages_path
mkdir -p $bin_path

# Install dataClay in a custom path
# TODO: Add `--install-option="--install-scripts=$PWD/bin"` to install scripts in a custom path
pip install -e ./dataclay/[bsc_mn,telemetry] --target $packages_path

# Move bin scripts to bin path
mv $packages_path/bin/* $bin_path
rm -rf $packages_path/bin

# NOTE: The sitecustomize.py script is needed for importing editable installs (like dataclay)
printf "import site\nsite.addsitedir('$(realpath $packages_path)')\n" >$packages_path/sitecustomize.py
