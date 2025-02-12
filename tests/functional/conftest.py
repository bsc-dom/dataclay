import os
import sys

import grpc
import pytest


@pytest.fixture(scope="session")
def python_version():
    return f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture(scope="session")
def docker_setup(python_version, request):
    legacy_deps = request.config.getoption("--build-legacy-deps")
    legacy_arg = f" --build-arg LEGACY_DEPS=True " if legacy_deps else " "
    return [
        f"build{ legacy_arg }--build-arg PYTHON_VERSION={python_version}-bookworm",
        "up -d",
    ]


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "tests/functional", "docker-compose.yml")


@pytest.fixture(scope="session")
def deploy_dataclay(docker_ip, docker_services):
    """Ensure that services are up and responsive."""

    mds_port = docker_services.port_for("metadata-service", 16587)
    grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{mds_port}")).result(timeout=10)

    # TODO: Wait for the backend to be ready before starting the tests
    # NOTE: Below code is not working since it is not the correct ip
    # The ip is masked by the docker-compose network
    # backend_port = docker_services.port_for("backend", 6867)
    # grpc.channel_ready_future(grpc.insecure_channel(f"127.0.0.1:{backend_port}")).result(timeout=10)


@pytest.fixture(scope="session")
def client(deploy_dataclay):
    import dataclay

    client = dataclay.Client(host="127.0.0.1")
    client.start()
    yield client
    client.stop()
