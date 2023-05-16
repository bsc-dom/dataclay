# Orchestration
Scripts for orchestrating dataClay in MareNostrum 4 (MN4)


First, modify the `config.sh` to update the **DATACLAY_VERSION** and the **BSC_USER**.

The `sync-to-mn4.sh` is used to copy the dataCay source and the orchestration scripts into MN4.

The `install-to-mn4.sh` is used to install dataClay and its dependencies (redis) into MN4. 
This script uses the `login0` which requires to be connected to BSC LAN (using VPN).


## Extra

Download latest binary release of Opentelemetry Collector Contrib, and save it in bin folder.
Current version is not working properly with "otlpjsonfile" receiver. Compile it instead from https://github.com/open-telemetry/opentelemetry-collector-contrib.

https://github.com/open-telemetry/opentelemetry-collector-releases/releases

Download latest binary release of ETCD and save it in bin folder.

https://github.com/etcd-io/etcd/releases

Or use the corresponding scripts from /utils




