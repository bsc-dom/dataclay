# Orchestration

Scripts for orchestrating dataClay in MareNostrum5 (MN5)

First, modify the `VERSION` file to update the **DATACLAY_VERSION**.

The `sync_all.sh` is used to copy the dataCay source and the orchestration scripts into MN5.

The `install_all.sh` is used to install dataClay and its dependencies (redis, opentelemetry) into MN5.
This script uses the `glogin4` node which requires to be connected to BSC LAN (using VPN).

The `sync_examples.sh` is used to copy only the examples into MN5.
