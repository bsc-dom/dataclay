from pytest_bdd import scenario, scenarios, given, when, then, parsers
from dataclay import api

# from model.company import Company, Person
import pytest

# from test_make_persistent import *

# scenarios("../../features")


@pytest.fixture
def context():
    return {}


@pytest.fixture
def mock_env_client(monkeypatch):
    monkeypatch.setenv("METADATA_SERVICE_HOST", "127.0.0.1")
    monkeypatch.setenv("DC_USERNAME", "user")
    monkeypatch.setenv("DC_PASSWORD", "s3cret")
    monkeypatch.setenv("DEFAULT_DATASET", "myDataset")


@given("session is initialized")
@when("start a new session")
def new_session(mock_env_client):
    api.init()


@given("I finish the session")
def finish_session():
    api.finish()


@given(parsers.parse("'{class_name:w}' from '{module_path}' is imported"))
def import_class(monkeypatch, class_name, module_path):
    from importlib import import_module

    module = import_module(module_path)
    monkeypatch.setitem(globals(), class_name, getattr(module, class_name))


@when(
    parsers.parse("create a '{class_name:w}' object with '{args}' params"),
    target_fixture="dc_object",
)
@when(
    parsers.parse("create '{obj_name:w}' object of class '{class_name:w}' with '{args}' params"),
    target_fixture="dc_object",
)
def new_dataclay_object(context, class_name, args=None, obj_name=None):
    klass = globals()[class_name]
    obj = klass("Alice", 23)
    if obj_name is not None:
        context[obj_name] = obj
    return obj
