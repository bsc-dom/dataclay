===========
HPC Tracing
===========

How to generate paraver traces in MN5
=====================================

Using COMPSs
------------
In order to get the traces we will create a script.

- First we have to import the COMPSs and DataClay modules in order to be able to use them, as well as defining which python version we will be using:

.. code-block:: bash

	export COMPSS_PYTHON_VERSION=3
	module load COMPSs/3.3
	module load dataclay/edge

- After importing those modules we can call the COMPSs script "enqueue_compss" which will automatically send the job to the MN5, adding the necessary options:

.. code-block:: bash

	##########
	# USAGE: #
	##########
	###################################################################################################
	# >$ enqueue_comps [queue_system_options] [COMPSs_options] application_name application_arguments #
	###################################################################################################
	
	enqueue_compss \
		--storage_home=$DATACLAY_HOME/storage/ \
		--storage_props=$DATACLAY_HOME/storage/storage_props_example \
		--classpath=$DATACLAY_HOME/storage/StorageItf-1.0.jar \
		--pythonpath=$DATACLAY_PYTHONPATH \
		--qos=gp_debug \
		--project_name="XXXXX" \
		application_name.py

This will generate a trace for each one of the nodes in the directory "$HOME/.COMPSs/[SLURM_JOB_ID]/trace/". 
Something like this:

	master_compss_trace.tar.gz			
	
	static_gs20r2b02-ib0_compss_trace.tar.gz
	
	static_gs20r2b01-ib0_compss_trace.tar.gz

In order to generate the paraver files, we will call another COMPSs script, "compss_gentrace". We can create another quick script to do it.

.. code-block:: bash

	module load COMPSs/3.3

	compss_gentrace

If we run this script in the same directory where we found the traces ($HOME/.COMPSs/[SLURM_JOB_ID]/trace/), the paraver files will appear.

How to inspect the traces in Paraver
====================================
To be able to see these files we will have to open them using the following commands:

.. code-block:: bash

	#load paraver module
	module load paraver
	#You should get this response: load paraver/latest (PATH)

.. code-block:: bash

	#run paraver application
	wxparaver trace.prv

Paraver will display a small interface

.. hint::

	If you get this error message `Error: Unable to initialize GTK+, is DISPLAY set properly?`
	
	Try adding the **-X** option in your ssh connection.
	`Example: ssh -X bscXXXXXX@gloginX.bsc.es`

- Then you have to press File>Load Configuration. There you can load the configuration you need. 

- COMPSs have some configurations you can use. 

  To access their configurations you have to search in /gpfs/apps/MN5/GPP/COMPSs/3.3/Dependencies/paraver/cfgs/

.. tip::
	
	Load the compss_runtime.cfg and the compss_tasks.cfg

	Those traces are easy to interpret and will help you understand how it works.
