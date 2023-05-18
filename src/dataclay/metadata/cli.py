import argparse
import logging
import os

import grpc

from dataclay.metadata.client import MetadataClient

DATACLAY_LOGLEVEL = os.getenv("DATACLAY_LOGLEVEL", default="WARNING").upper()
logging.basicConfig(level=DATACLAY_LOGLEVEL)
logger = logging.getLogger(__name__)

# TODO: Use configparse to read connection details from config file
DATACLAY_METADATA_HOSTNAME = os.getenv("DATACLAY_METADATA_HOSTNAME") or os.environ["DC_HOST"]

DATACLAY_METADATA_PORT = int(os.getenv("DATACLAY_METADATA_PORT", "16587"))


def new_account(args):
    logger.info(f'Creating "{args.username}" account')
    try:
        mds_client = MetadataClient(DATACLAY_METADATA_HOSTNAME, DATACLAY_METADATA_PORT)
        mds_client.new_account(args.username, args.password)
    except grpc.RpcError as e:
        logger.error(e.details())
        logger.debug(e.code().name)
    else:
        logger.info(f"Created account ({args.username})")


def new_session(args):
    logger.info(f"Creating new session")
    try:
        mds_client = MetadataClient(DATACLAY_METADATA_HOSTNAME, DATACLAY_METADATA_PORT)
        response = mds_client.new_session(
            args.username, args.password, args.datasets.split(":"), args.default_dataset
        )
    except grpc.RpcError as e:
        logger.error(e.details())
        logger.debug(e.code().name)
    else:
        logger.info(f"Created new session for {args.username}, with id {response.id}")


def new_dataset(args):
    logger.info(f"Creating new dataset")
    try:
        mds_client = MetadataClient(DATACLAY_METADATA_HOSTNAME, DATACLAY_METADATA_PORT)
        mds_client.new_dataset(args.username, args.password, args.dataset)
    except grpc.RpcError as e:
        logger.error(e.details())
        logger.debug(e.code().name)
    else:
        logger.info(f"Created new dataset {args.dataset} for {args.username}")


def get_backends(args):
    pass


def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser(description="Dataclay tool")
    # TODO: Remove "dest" for new python versions
    subparsers = parser.add_subparsers(dest="function", required=True)

    # Create the parser for the "new_account" command
    parser_new_account = subparsers.add_parser("new_account")
    parser_new_account.add_argument("username", type=str)
    parser_new_account.add_argument("password", type=str)
    parser_new_account.set_defaults(func=new_account)

    # Create the parser for the "new_session" command
    parser_new_session = subparsers.add_parser("new_session")
    parser_new_session.add_argument("username", type=str)
    parser_new_session.add_argument("password", type=str)
    parser_new_session.add_argument("default_dataset", type=str)
    parser_new_session.set_defaults(func=new_session)

    # Create the parser for the "new_dataset" command
    parser_new_dataset = subparsers.add_parser("new_dataset")
    parser_new_dataset.add_argument("username", type=str)
    parser_new_dataset.add_argument("password", type=str)
    parser_new_dataset.add_argument("dataset", type=str)
    parser_new_dataset.set_defaults(func=new_dataset)

    # Create the parser for the "get_backends" command
    parser_new_account = subparsers.add_parser("get_backends")
    parser_new_account.add_argument("username", type=str)
    parser_new_account.add_argument("password", type=str)
    parser_new_account.set_defaults(func=get_backends)

    # TODO: Create the parser for the other commands

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
