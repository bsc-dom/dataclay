# Wordcount Application

This application presents the wordcount algorithm parallelized with
PyCOMPSs and using persistent storage backend to deal with multiple blocks
of text.

This application is composed of the following files:

```text
src
  |- model
  |    |- __init__.py
  |    |- block.py
  |- storage_model
  |    |- __init__.py
  |    |- block.py
  |
  |- wordcount.py

dataset
  |- ...
```

The ```src/wordcount.py``` file contains the main of the Wordcount algorithm,
while the ```src/model/block.py``` contains the declaration of the Words
class with its necessary methods for text addition and retrieval, and the
```src/model/block.py``` contains the declaration of the Words class for the
persistent storage framework.

In addition, this application also contains a set of scripts to submit the
```wordcount.py``` application within the <ins>MN5 supercomputer</ins>
queuing system for **dataClay**.
The following commands submit the execution *without a job dependency*,
requesting *2 nodes*, with *5 minutes* walltime and with *tracing and graph
generation disabled* to perform the wordcount of the dataset stored in the
```dataset``` folder.

* Launch with dataClay:

  ```bash
  ./launch_with_dataClay.sh None 2 5 false $(pwd)/src/wordcount.py -d $(pwd)/dataset
  ```

* Also, contains a script to run the ```wordcount.py``` application <ins>locally</ins> with **dataClay** to perform the wordcount of the  dataset stored in the ```dataset``` folder:

  ```bash
  ./run_with_dataClay.sh
  ```

Furthermore, it can also be launched or executed without persistent storage
backend with the same parameters:

* Launch without **dataClay**:

  ```bash
  ./launch.sh None 2 5 false $(pwd)/src/wordcount.py -d 
  ```

* Run the ```hello_world.py``` application <ins>locally</ins> without **dataClay**:

  ```bash
  ./run.sh
  ```

## Available options

```
 -d <DATASET_PATH>....... Path where the dataset files are
 --use_storage.......... Use the available storage backend
```

## Issues

If any issue is found, please contact <support-compss@bsc.es>
