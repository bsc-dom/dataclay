import argparse
import json
import logging
import os
import pprint

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from dataclay.backend.client import BackendClient
from dataclay.metadata.client import MetadataClient
from dataclay.utils.uuid import UUIDEncoder, uuid_parser

DATACLAY_LOGLEVEL = os.getenv("DATACLAY_LOGLEVEL", default="INFO").upper()
logging.basicConfig(level=DATACLAY_LOGLEVEL)
logger = logging.getLogger(__name__)


def healthcheck(host, port, service):
    with grpc.insecure_channel("%s:%s" % (host, port)) as channel:
        health_stub = health_pb2_grpc.HealthStub(channel)
        request = health_pb2.HealthCheckRequest(service=service)
        resp = health_stub.Check(request)

        if resp.status != health_pb2.HealthCheckResponse.SERVING:
            raise ConnectionError("Service %s not available" % service)


def new_account(username, password, host, port):
    logger.info(f'Creating "{username}" account')
    mds_client = MetadataClient(host, port)
    mds_client.new_account(username, password)
    logger.info("Created account (%s)", username)


def new_session(username, password, dataset, host, port):
    logger.info("Creating new session")
    mds_client = MetadataClient(host, port)
    session = mds_client.new_session(username, password, dataset)
    logger.info("Created new session for %s, with id %s", username, session.id)


def new_dataset(username, password, dataset, host, port):
    logger.info("Creating new dataset")
    mds_client = MetadataClient(host, port)
    mds_client.new_dataset(username, password, dataset)
    logger.info("Created new dataset %s for %s", dataset, username)


def get_backends(host, port):
    metadata_client = MetadataClient(host, port)
    backend_infos = metadata_client.get_all_backends()
    for v in backend_infos.values():
        print(json.dumps(v.__dict__, cls=UUIDEncoder, indent=2))


def new_backend(args):
    pass


def stop_backend(host, port):
    backend_client = BackendClient(host, port)
    backend_client.stop()
    pass


def stop_dataclay(host, port):
    metadata_client = MetadataClient(host, port)
    backend_infos = metadata_client.get_all_backends()
    for v in backend_infos.values():
        stop_backend(v.host, v.port)

    metadata_client.stop()


def rebalance(host, port):
    metadata_client = MetadataClient(host, port)
    backend_infos = metadata_client.get_all_backends()

    # Get backend clients
    backend_clients = {}
    for id, info in backend_infos.items():
        backend_client = BackendClient(info.host, info.port)
        if backend_client.is_ready(5):
            backend_clients[id] = backend_client

    object_mds = metadata_client.get_all_objects()
    num_objects = len(object_mds)
    mean = num_objects // len(backend_clients)

    print("Num backends:", len(backend_clients))
    print("Num objects:", num_objects)
    print("Avg objects per backend:", mean)

    backend_objects = {backend_id: [] for backend_id in backend_clients.keys()}
    for object_md in object_mds.values():
        backend_objects[object_md.master_backend_id].append(object_md.id)

    print("\nBefore rebalance:")
    backends_diff = {}
    for backend_id, objects in backend_objects.items():
        print(f"{backend_id}: {len(objects)}")
        diff = len(objects) - mean
        backends_diff[backend_id] = diff

    for backend_id, object_ids in backend_objects.items():
        if backends_diff[backend_id] <= 0:
            continue
        for new_backend_id in backend_objects.keys():
            if backend_id == new_backend_id or backends_diff[new_backend_id] >= 0:
                continue
            while backends_diff[backend_id] > 0 and backends_diff[new_backend_id] < 0:
                object_id = object_ids.pop()
                backend_client = backend_clients[backend_id]
                backend_client.move_object(object_id, new_backend_id, None)
                backends_diff[backend_id] -= 1
                backends_diff[new_backend_id] += 1

    print("\nAfter rebalance:")
    for backend_id, diff in backends_diff.items():
        print(f"{backend_id}: {mean+diff}")


def get_objects(host, port):
    metadata_client = MetadataClient(host, port)
    object_mds = metadata_client.get_all_objects()
    for v in object_mds.values():
        print(json.dumps(v.__dict__, cls=UUIDEncoder, indent=2))


def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(description="Dataclay tool")
    subparsers = parser.add_subparsers(dest="function", required=True)
    # parser.add_argument("--host", type=str, default="localhost", help="Specify the host (default: localhost)")
    # parser.add_argument("--port", type=int, default=16587, help="Specify the port (default: 16587)")

    # Create the parser for the "healthcheck" command
    parser_healthcheck = subparsers.add_parser("healthcheck")
    parser_healthcheck.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_healthcheck.add_argument(
        "--service",
        choices=["backend", "metadata"],
        required=True,
        help="Specify the kind of service",
    )
    parser_healthcheck.add_argument(
        "--port", type=int, default=0, help="Specify the port (default: inferred from service)"
    )

    # Create the parser for the "new_account" command
    parser_new_account = subparsers.add_parser("new_account")
    parser_new_account.add_argument("username", type=str)
    parser_new_account.add_argument("password", type=str)
    parser_new_account.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_new_account.add_argument(
        "--port", type=int, default=16587, help="Specify the port (default: 16587)"
    )

    # Create the parser for the "new_session" command
    parser_new_session = subparsers.add_parser("new_session")
    parser_new_session.add_argument("username", type=str)
    parser_new_session.add_argument("password", type=str)
    parser_new_session.add_argument("dataset", type=str)
    parser_new_session.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_new_session.add_argument(
        "--port", type=int, default=16587, help="Specify the port (default: 16587)"
    )

    # Create the parser for the "new_dataset" command
    parser_new_dataset = subparsers.add_parser("new_dataset")
    parser_new_dataset.add_argument("username", type=str)
    parser_new_dataset.add_argument("password", type=str)
    parser_new_dataset.add_argument("dataset", type=str)
    parser_new_dataset.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_new_dataset.add_argument(
        "--port", type=int, default=16587, help="Specify the port (default: 16587)"
    )

    # Create the parser for the "get_backends" command
    parser_get_backends = subparsers.add_parser("get_backends")
    parser_get_backends.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_get_backends.add_argument(
        "--port", type=int, default=16587, help="Specify the port (default: 16587)"
    )

    # Create the parser for the "stop_backend" command
    parser_stop_backend = subparsers.add_parser("stop_backend")
    parser_stop_backend.add_argument("host", type=str, help="Specify the backend host")
    parser_stop_backend.add_argument(
        "port", nargs="?", type=int, default=6867, help="Specify the backend port (default: 6867)"
    )

    # Create the parser for the "rebalance" command
    parser_rebalance = subparsers.add_parser("rebalance")
    parser_rebalance.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_rebalance.add_argument(
        "--port", type=int, default=16587, help="Specify the port (default: 16587)"
    )

    # Create the parser for the "stop_dataclay" command
    parser_stop_dataclay = subparsers.add_parser("stop_dataclay")
    parser_stop_dataclay.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_stop_dataclay.add_argument(
        "--port", type=int, default=16587, help="Specify the port (default: 16587)"
    )

    # Create the parser for the "get_objects" command
    parser_get_objects = subparsers.add_parser("get_objects")
    parser_get_objects.add_argument(
        "--host", type=str, default="localhost", help="Specify the host (default: localhost)"
    )
    parser_get_objects.add_argument(
        "--port", type=int, default=16587, help="Specify the port (default: 16587)"
    )

    # TODO: Create the parser for the other commands

    args = parser.parse_args()

    if args.function == "healthcheck":
        if args.service == "backend":
            port = args.port or 6867
            healthcheck(args.host, port, "dataclay.proto.backend.BackendService")
        elif args.service == "metadata":
            port = args.port or 16587
            healthcheck(args.host, port, "dataclay.proto.metadata.MetadataService")

    elif args.function == "new_account":
        new_account(args.username, args.password, args.host, args.port)

    elif args.function == "new_session":
        new_session(args.username, args.password, args.dataset, args.host, args.port)

    elif args.function == "new_dataset":
        new_dataset(args.username, args.password, args.dataset, args.host, args.port)

    elif args.function == "stop_backend":
        stop_backend(args.host, args.port)

    elif args.function == "stop_dataclay":
        stop_dataclay(args.host, args.port)

    elif args.function == "rebalance":
        rebalance(args.host, args.port)

    elif args.function == "get_backends":
        get_backends(args.host, args.port)

    elif args.function == "get_objects":
        get_objects(args.host, args.port)

    # args.func(args)


if __name__ == "__main__":
    main()
