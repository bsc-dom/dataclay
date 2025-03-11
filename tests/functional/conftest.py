import os

import grpc
import pytest


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "tests/functional", "docker-compose.yml")


@pytest.fixture(scope="session")
def wait_dataclay(mds_connection):
    """Ensure that services are up and responsive."""

    mds_host, mds_port = mds_connection
    grpc.channel_ready_future(grpc.insecure_channel(f"{mds_host}:{mds_port}")).result(timeout=10)

    # TODO: Wait for the backend to be ready before starting the tests
    # NOTE: Below code is not working since it is not the correct ip
    # The ip is masked by the docker-compose network
    # backend_port = docker_services.port_for("backend", 6867)
    # grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{backend_port}")).result(timeout=10)


@pytest.fixture(scope="session")
def client(wait_dataclay, mds_connection):
    import dataclay

    mds_host, mds_port = mds_connection
    client = dataclay.Client(host=mds_host, port=mds_port)
    client.start()
    yield client
    client.stop()
