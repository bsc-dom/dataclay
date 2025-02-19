import sys

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
def proxy_connection(docker_ip, docker_services):
    proxy_port = docker_services.port_for("proxy", 8676)
    return "127.0.0.1", proxy_port


@pytest.fixture(scope="session")
def mds_connection(docker_ip, docker_services):
    mds_port = docker_services.port_for("metadata-service", 16587)
    return "127.0.0.1", mds_port


def pytest_addoption(parser):
    parser.addoption(
        "--build-legacy-deps",
        action="store_true",
        help="Build docker image with legacy dependencies",
    )
