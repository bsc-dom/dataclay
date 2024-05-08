#!/bin/bash

set -e

# Load python module
python_full_version="${1:-3.12.1}"
major_minor_version="${python_full_version%.*}"
module load mkl intel hdf5 "python/$python_full_version"

# Define paths
lib_path="./lib/python$major_minor_version"
packages_path="$lib_path/site-packages"
bin_path="$lib_path/bin"

# Remove previous installations
rm -rf $lib_path
mkdir -p $packages_path
mkdir -p $bin_path

# Install dataClay in a custom path
# TODO: Add `--install-option="--install-scripts=$PWD/bin"` to install scripts in a custom path
pip install -e ./dataclay/[bsc_mn,telemetry] --target $packages_path

# Create sitecustomize.py script for importing editable installs
printf "import site\nsite.addsitedir('$(realpath $packages_path)')\n" >$packages_path/sitecustomize.py
