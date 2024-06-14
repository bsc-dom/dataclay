Using dataClay for persistent data
==================================

This example shows how persistence (i.e., across restarts) can be managed with a simple 
`docker compose`-based deployment.

Starting for the first time
---------------------------

`docker compose up` will start everything. Note that several folders will be created,
which will contain persistent data:

- `backend-alpha-data` contains objects stored in the BackendAlpha
- `backend-bravo-data` contains objects stored in the BackendBeta
- `redis-data` contains the metadata (i.e. the Redis key-value persistent data)

Those folders will be created by the docker daemon, so they may belong to the root user.

You can run the `client.py` example, which will creae and populate a `Family` object.

If you run this `client.py` again it will print its contents.

Restarting the system
---------------------

A `docker compose down` will stop the system and (because by default it does not _kill_
he containers but _term_-inates them) all data will be persisted into the filesystem.

Note that if the dataClay backends are forcefully killed, then some data may be lost.

When starting again the containers (by issuing a `docker compose up`) the system will
realize that there is persisted objects (because metadata and object data are both in
the filesystem and reachable).

If you run the `client.py` you will obtain the contens of the `Family` object, which
was persisted before.

Starting from scratch
---------------------

You need to remove the data folders mentioned above. Because the data folders are created
by the docker daemon and may belong to the root user, you may need o use `sudo` to remove
them.

Once you remove those data folders, all conainers will start with no prior knowledge.
