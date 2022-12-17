from dataclay import api
import uuid
import time
import subprocess
import os
import pytest


@pytest.fixture(scope="session")
def dataclay_path(tmp_path_factory):
    dataclay_path = tmp_path_factory.mktemp("dataclay")
    storage_path = dataclay_path / "storage"
    storage_path.mkdir()
    return dataclay_path


@pytest.fixture(scope="session")
def start_etcd(dataclay_path):
    etcd = subprocess.Popen(["etcd", "--data-dir", "metadata.etcd"], cwd=dataclay_path)
    subprocess.run(["etcdctl", "put", "/this", str(uuid.uuid4())])
    time.sleep(1)
    yield etcd
    etcd.kill()


@pytest.fixture(scope="session")
def start_mds(start_etcd, dataclay_path):
    env = os.environ | {"ETCD_HOST": "127.0.0.1", "STORAGE_PATH": f"{dataclay_path}/storage"}
    mds = subprocess.Popen(["python", "-m", "dataclay.metadata"], env=env, cwd=dataclay_path)
    time.sleep(1)
    yield mds
    mds.kill()


@pytest.fixture(scope="session")
def start_backend(start_mds, dataclay_path):
    env = os.environ | {"ETCD_HOST": "127.0.0.1", "STORAGE_PATH": f"{dataclay_path}/storage"}
    backend = subprocess.Popen(
        ["python", "-m", "dataclay.backend"], env=env, cwd="tests/functional"
    )
    time.sleep(1)

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
    yield backend
    backend.kill()


# @pytest.fixture(scope="session")
# def start_dataclay(tmp_path_factory):

#     etcd = subprocess.Popen(["etcd", "--data-dir", f"{tmp_path_factory}/metadata.etcd"])
#     subprocess.run(["etcdctl", "put", "/this", str(uuid.uuid4())])
#     time.sleep(1)

#     env = os.environ | {"ETCD_HOST": "127.0.0.1", "STORAGE_PATH": f"{tmp_path_factory}/storage"}
#     mds = subprocess.Popen(["python", "-m", "dataclay.metadata"], env=env)
#     time.sleep(1)

#     backend = subprocess.Popen(["python", "-m", "dataclay.backend"], env=env)
#     time.sleep(1)

#     env = os.environ | {"METADATA_SERVICE_HOST": "127.0.0.1"}

#     subprocess.run(
#         ["python", "-m", "dataclay.metadata.cli", "new_account", "user", "s3cret"], env=env
#     )
#     subprocess.run(
#         ["python", "-m", "dataclay.metadata.cli", "new_dataset", "user", "s3cret", "myDataset"],
#         env=env,
#     )
#     subprocess.run(
#         ["python", "-m", "dataclay.metadata.cli", "new_dataset", "user", "s3cret", "auxDataset"],
#         env=env,
#     )

#     yield 123
#     backend.kill()
#     mds.kill()
#     etcd.kill()


@pytest.fixture
def mock_env_client(start_backend, monkeypatch):
    monkeypatch.setenv("METADATA_SERVICE_HOST", "127.0.0.1")
    monkeypatch.setenv("DC_USERNAME", "user")
    monkeypatch.setenv("DC_PASSWORD", "s3cret")
    monkeypatch.setenv("DEFAULT_DATASET", "myDataset")


@pytest.fixture
def init_client(mock_env_client):
    yield api.init()
    api.finish()
