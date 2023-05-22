#!/bin/bash

set -e

PYTHON_VERSION="${1:-3.10.2}"
VENV_PATH=venv$PYTHON_VERSION
rm -rf $VENV_PATH

module load "python/$PYTHON_VERSION"
python -m venv $VENV_PATH
source $VENV_PATH/bin/activate
python -m pip install -e ./dataclay/[mn4,telemetry]
deactivate

SITE_PATH=$(find ~+/$VENV_PATH -name site-packages)
printf "import site\nsite.addsitedir('$SITE_PATH')\n" >$SITE_PATH/sitecustomize.py
