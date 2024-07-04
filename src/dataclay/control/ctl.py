import argparse
import asyncio
import json
import logging
import time

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

import dataclay
from dataclay.backend.client import BackendClient
from dataclay.config import ClientSettings, settings
from dataclay.metadata.client import MetadataClient
from dataclay.utils.uuid import UUIDEncoder

logger = logging.getLogger(__name__)


def healthcheck(host, port, service, retries=1, retry_interval=1.0):
    with grpc.insecure_channel("%s:%s" % (host, port)) as channel:
        for attempt in range(retries):
            try:
                health_stub = health_pb2_grpc.HealthStub(channel)
                request = health_pb2.HealthCheckRequest(service=service)
                resp = health_stub.Check(request)
                if resp.status == health_pb2.HealthCheckResponse.SERVING:
                    logger.info("Service %s at %s:%s is serving", service, host, port)
                    return
            except grpc.RpcError as e:
                if attempt == retries - 1:  # Last attempt
                    raise ConnectionError(
                        f"Service {service} at {host}:{port} not available after {retries} retries: {e}"
                    )

            # Wait before the next retry
            time.sleep(retry_interval)
        raise ConnectionError(
            f"Service {service} at {host}:{port} is not serving after {retries} retries"
        )


def new_account(username, password, host, port):
    logger.info("Creating new account %s at %s:%s", username, host, port)
    mds_client = MetadataClient(host, port)
    mds_client.new_account(username, password)


def new_dataset(username, password, dataset, host, port):
    logger.info("Creating new dataset %s/%s at %s:%s", username, dataset, host, port)
    mds_client = MetadataClient(host, port)
    mds_client.new_dataset(username, password, dataset)


async def get_backends(host, port):
    logger.info("Getting backends from %s:%s", host, port)
    metadata_client = MetadataClient(host, port)
    backend_infos = await metadata_client.get_all_backends()
    for v in backend_infos.values():
        print(json.dumps(v.__dict__, cls=UUIDEncoder, indent=2))


def new_backend(args):
    pass


async def stop_backend(host, port):
    logger.info("Stopping backend at %s:%s", host, port)
    backend_client = BackendClient(host, port)
    await backend_client.stop()


async def stop_dataclay(host, port):
    logger.info("Stopping dataclay at %s:%s", host, port)
    metadata_client = MetadataClient(host, port)
    backend_infos = await metadata_client.get_all_backends()
    for v in backend_infos.values():
        await stop_backend(v.host, v.port)

    await metadata_client.stop()


def rebalance(host, port):
    logger.info("Rebalancing dataclay at %s:%s", host, port)
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


async def flush_all(host, port):
    logger.info("Flushing all data from %s:%s", host, port)
    backend_client = BackendClient(host, port)
    await backend_client.flush_all()


async def get_objects(host, port):
    logger.info("Getting objects from %s:%s", host, port)
    metadata_client = MetadataClient(host, port)
    object_mds = await metadata_client.get_all_objects()
    for v in object_mds.values():
        print(json.dumps(v.__dict__, cls=UUIDEncoder, indent=2))


def parse_arguments():
    # Create the top-level parser
    parser = argparse.ArgumentParser(description="Dataclay tool")
    parser.add_argument("--version", action="version", version=f"%(prog)s {dataclay.__version__}")
    subparsers = parser.add_subparsers(dest="function", required=True, help="Function to execute")

    # Common arguments for host and port
    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument(
        "--host",
        type=str,
        default=settings.client.dataclay_host,
        help="Specify the dataclay host (default: DC_HOST or localhost)",
    )
    common_args.add_argument(
        "--port",
        type=int,
        default=settings.client.dataclay_port,
        help="Specify the dataclay port (default: DC_PORT or 16587)",
    )

    ###############
    # healthcheck #
    ###############
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

    ###############
    # new_account #
    ###############
    parser_new_account = subparsers.add_parser("new_account", parents=[common_args])
    parser_new_account.add_argument("username", type=str, help="Specify the username")
    parser_new_account.add_argument("password", type=str, help="Specify the password")

    ###############
    # new_dataset #
    ###############
    parser_new_dataset = subparsers.add_parser("new_dataset", parents=[common_args])
    parser_new_dataset.add_argument(
        "--username",
        type=str,
        default=settings.client.username,
        help="Specify the username (default: DC_USERNAME or admin)",
    )
    parser_new_dataset.add_argument(
        "--password",
        type=str,
        default=settings.client.password,
        help="Specify the password (default: DC_PASSWORD or admin)",
    )
    parser_new_dataset.add_argument(
        "--dataset",
        type=str,
        default=settings.client.dataset,
        help="Specify the dataset (default: DC_DATASET or admin)",
    )

    ################
    # get_backends #
    ################
    parser_get_backends = subparsers.add_parser("get_backends", parents=[common_args])

    #############
    # rebalance #
    #############
    parser_rebalance = subparsers.add_parser("rebalance", parents=[common_args])

    ##############
    # flush_all #
    ##############
    parser_flush_all = subparsers.add_parser("flush_all")
    parser_flush_all.add_argument(
        "--host", type=str, required=True, help="Specify the backend host"
    )
    parser_flush_all.add_argument(
        "--port", type=int, default=6867, help="Specify the backend port (default: 6867)"
    )

    ################
    # stop_backend #
    ################
    # TODO: Improve this?
    parser_stop_backend = subparsers.add_parser("stop_backend")
    parser_stop_backend.add_argument(
        "--host", type=str, required=True, help="Specify the backend host"
    )
    parser_stop_backend.add_argument(
        "--port", type=int, default=6867, help="Specify the backend port (default: 6867)"
    )

    #################
    # stop_dataclay #
    #################
    parser_stop_dataclay = subparsers.add_parser("stop_dataclay", parents=[common_args])

    ###############
    # get_objects #
    ###############
    parser_get_objects = subparsers.add_parser("get_objects", parents=[common_args])

    return parser.parse_args()


async def main():
    # Set client settings
    settings.client = ClientSettings()

    # Parse arguments
    args = parse_arguments()

    # Run the function
    if args.function == "healthcheck":
        if args.service == "backend":
            port = args.port or 6867
            healthcheck(args.host, port, "dataclay.proto.backend.BackendService")
        elif args.service == "metadata":
            port = args.port or 16587
            healthcheck(args.host, port, "dataclay.proto.metadata.MetadataService")

    elif args.function == "new_account":
        new_account(args.username, args.password, args.host, args.port)

    elif args.function == "new_dataset":
        new_dataset(args.username, args.password, args.dataset, args.host, args.port)

    elif args.function == "stop_backend":
        await stop_backend(args.host, args.port)

    elif args.function == "stop_dataclay":
        await stop_dataclay(args.host, args.port)

    elif args.function == "rebalance":
        rebalance(args.host, args.port)

    elif args.function == "flush_all":
        await flush_all(args.host, args.port)

    elif args.function == "get_backends":
        await get_backends(args.host, args.port)

    elif args.function == "get_objects":
        await get_objects(args.host, args.port)


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
