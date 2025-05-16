import sys

import pytest


@pytest.fixture(scope="session")
def python_version():
    return f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture(scope="session")
def docker_setup(python_version, request):
    return [
        f"build --build-arg PYTHON_VERSION={python_version}-bookworm",
        "up -d",
    ]


@pytest.fixture(scope="session")
def proxy_connection(docker_ip, docker_services):
    proxy_port = docker_services.port_for("proxy", 8676)
    return docker_ip, proxy_port


@pytest.fixture(scope="session")
def mds_connection(docker_ip, docker_services):
    mds_port = docker_services.port_for("metadata-service", 16587)
    return docker_ip, mds_port


def pytest_addoption(parser):
    parser.addoption(
        "--build-legacy-deps",
        action="store_true",
        help="Build docker image with legacy dependencies",
    )
