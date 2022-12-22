import dataclay
import time
import subprocess
import os
import pytest


@pytest.fixture(scope="session")
def docker_compose_command():
    return "docker compose"


@pytest.fixture(scope="session")
def http_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    # port = docker_services.port_for("httpbin", 80)
    # url = "http://{}:{}".format(docker_ip, port)
    # docker_services.wait_until_responsive(
    #     timeout=30.0, pause=0.1, check=lambda: is_responsive("127.0.0.1", 2379, 1)
    # )
    time.sleep(5)

    env = os.environ | {"METADATA_SERVICE_HOST": "127.0.0.1"}

    subprocess.run(
        ["python", "-m", "dataclay.metadata.cli", "new_account", "user", "s3cret"], env=env
    )
    subprocess.run(
        ["python", "-m", "dataclay.metadata.cli", "new_dataset", "user", "s3cret", "myDataset"],
        env=env,
    )
    subprocess.run(
        ["python", "-m", "dataclay.metadata.cli", "new_dataset", "user", "s3cret", "auxDataset"],
        env=env,
    )

    return "hello"


@pytest.fixture(scope="session")
def init_client(http_service):
    client = dataclay.client(
        host="127.0.0.1", username="user", password="s3cret", dataset="myDataset"
    )
    client.start()
    yield client
    client.stop()
