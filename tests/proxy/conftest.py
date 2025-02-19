import os

import grpc
import pytest


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "tests/proxy", "docker-compose.yml")


@pytest.fixture(scope="session")
def wait_dataclay(proxy_connection):
    """Ensure that services are up and responsive."""

    proxy_host, proxy_port = proxy_connection
    grpc.channel_ready_future(grpc.insecure_channel(f"{proxy_host}:{proxy_port}")).result(timeout=10)

    # backend_port = docker_services.port_for("backend", 6867)
    # grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{backend_port}")).result(timeout=10)

