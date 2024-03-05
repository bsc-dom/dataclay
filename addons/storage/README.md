# Storage API

## Packaging

```bash
mvn package
java -cp target/StorageItf-1.0-SNAPSHOT.jar storage.StorageItf 
```

## To use enqueue_compss

First load dataclay

```bash
module load DATACLAY
module load COMPSs
```

Then call:

```bash
enqueue_compss \
--storage_home=$DATACLAY_HOME/storage/ \
--storage_props=$DATACLAY_HOME/storage/storage_props_example \
--classpath=$DATACLAY_HOME/storage/StorageItf-1.0.jar \
--pythonpath=$DATACLAY_PYTHONPATH \
--qos=debug \
client.py
```

<!-- --lang=python path/to/dataclay/script -->
