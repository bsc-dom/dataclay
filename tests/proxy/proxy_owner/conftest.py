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
    return os.path.join(str(pytestconfig.rootdir), "tests/proxy", "docker-compose.yml")


@pytest.fixture(scope="session")
def deploy_dataclay(docker_ip, docker_services):
    """Ensure that services are up and responsive."""

    proxy_port = docker_services.port_for("proxy", 8676)
    grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{proxy_port}")).result(timeout=10)

    # backend_port = docker_services.port_for("backend", 6867)
    # grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{backend_port}")).result(timeout=10)


@pytest.fixture(scope="session")
def client(deploy_dataclay):
    client = dataclay.Client(proxy_host="127.0.0.1", username="Alex", password="s3cret")
    client.start()
    yield client
    client.stop()
