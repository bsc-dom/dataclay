from dataclay import api
import pytest


@pytest.fixture
def mock_env_client(monkeypatch):
    monkeypatch.setenv("METADATA_SERVICE_HOST", "127.0.0.1")
    monkeypatch.setenv("DC_USERNAME", "user")
    monkeypatch.setenv("DC_PASSWORD", "s3cret")
    monkeypatch.setenv("DEFAULT_DATASET", "myDataset")


@pytest.fixture
def init_client(mock_env_client):
    api.init()
