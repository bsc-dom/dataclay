# Hello world Application

This application presents the basic usage of persistent storage with PyCOMPSs.

To this end, shows how to declare tasks and persistent objects and how
they can be used transparently as task parameters.

This application is composed of two main files:

```text
src
  |- model
  |    |- __init__.py
  |    |- classes.py
  |- storage_model
  |    |- __init__.py
  |    |- classes.py
  |
  |- hello_world.py
```

More in detail, this application declares three tasks within the
```src/hello_world.py``` file:

1. **create_greeting**: Receives an string and instantiates a persistent object
with the string.
2. **greet**: Receives the persistent object and retrieves its content using an
object method.
3. **check_greeting**: Compares the initial message and the persistent object
content.

And the persistent object declaration can be found in the
```src/storage_model/classes.py```.

In addition, this application also contains a set of scripts to submit the
```hello_world.py``` application within the <ins>MN5 supercomputer</ins>
queuing system for **dataClay**.
The following commands submit the execution *without a job dependency*,
requesting *2 nodes*, with *5 minutes* walltime and with *tracing and graph
generation disabled*.

* Launch with **dataClay**:

  ```bash
  ./launch_with_dataClay.sh None 2 5 false $(pwd)/src/hello_world.py
  ```

* Also, contains a script to run the ```hello_world.py``` application
  <ins>locally</ins> with **dataClay**:

  ```bash
  ./run_with_dataClay.sh
  ```

Furthermore, it can also be launched or executed without persistent storage
backend with the same parameters:

* Launch without **dataClay**:

  ```bash
  ./launch.sh None 2 5 false $(pwd)/src/hello_world.py
  ```

* Run the ```hello_world.py``` application <ins>locally</ins> without **dataClay**:

  ```bash
  ./run.sh
  ```

## Issues

If any issue is found, please contact <support-compss@bsc.es>
