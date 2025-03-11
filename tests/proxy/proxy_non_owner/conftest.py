import pytest

import dataclay


@pytest.fixture(scope="session")
def client(wait_dataclay, proxy_connection):
    proxy_host, proxy_port = proxy_connection
    client = dataclay.Client(
        proxy_host=proxy_host, proxy_port=proxy_port, username="Marc", password="s3cret"
    )
    client.start()
    yield client
    client.stop()
