#!/bin/bash

export EXTRAE_HOME=/opt/COMPSs/Dependencies/extrae/
gcc -L$EXTRAE_HOME/lib -I$EXTRAE_HOME/include extrae_wrapper.c -lpttrace --shared -o dataclay_extrae_wrapper.so
