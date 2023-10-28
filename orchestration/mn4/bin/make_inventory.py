#!/usr/bin/env python3

import argparse

if __name__ == "__main__":
    # Parse the arguments from the command line input
    parser = argparse.ArgumentParser(
        description="Generate an Ansible inventory file from input hostnames."
    )
    parser.add_argument(
        "--redis",
        nargs="+",
        required=True,
        help="List of redis hostnames, separated by space.",
    )
    parser.add_argument(
        "--metadata",
        nargs="+",
        required=True,
        help="List of metadata server hostnames, separated by space.",
    )
    parser.add_argument(
        "--backends",
        nargs="+",
        required=True,
        help="List of backend server hostnames, separated by space.",
    )

    args = parser.parse_args()

    redis_servers = args.redis
    metadata_servers = args.metadata
    backend_servers = args.backends

    # Building the inventory content
    inventory_content = ""

    # Adding [redis] hosts
    inventory_content += "[redis]\n"
    for server in redis_servers:
        inventory_content += f"{server}\n"

    inventory_content += "\n"

    # Adding [metadata] hosts
    inventory_content += "[metadata]\n"
    for server in metadata_servers:
        inventory_content += f"{server}\n"

    inventory_content += "\n"

    # Adding [backend] hosts
    inventory_content += "[backend]\n"
    for server in backend_servers:
        inventory_content += f"{server}\n"

    # Print the inventory content
    print(inventory_content)
