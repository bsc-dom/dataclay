import os
import subprocess
import time

import grpc
import pytest

import dataclay


@pytest.fixture(scope="session")
def docker_compose_command():
    return "docker compose"


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "tests/functional", "docker-compose.yml")


@pytest.fixture(scope="session")
def deploy_dataclay(docker_ip, docker_services):
    """Ensure that services are up and responsive."""

    mds_port = docker_services.port_for("metadata-service", 16587)
    grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{mds_port}")).result(timeout=10)

    # backend_port = docker_services.port_for("backend", 6867)
    # grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{backend_port}")).result(timeout=10)


@pytest.fixture(scope="session")
def client(deploy_dataclay):
    client = dataclay.Client(
        host="127.0.0.1", username="testuser", password="s3cret", dataset="testuser"
    )
    client.start()
    yield client
    client.stop()
