from dataclay import api
import pytest
from model.family import Family, Person, Dog


@pytest.fixture
def mock_env_client(monkeypatch):
    monkeypatch.setenv("METADATA_SERVICE_HOST", "127.0.0.1")
    monkeypatch.setenv("DC_USERNAME", "user")
    monkeypatch.setenv("DC_PASSWORD", "s3cret")
    monkeypatch.setenv("DEFAULT_DATASET", "myDataset")


def test_activemethod_argument_make_persistent(mock_env_client):
    """
    A dataclay object is made persistent when passed as an argument
    to an activemethod of a persistent object
    """
    api.init()

    family = Family()
    person = Person("Marc", 24)
    family.make_persistent()
    assert person.is_persistent == False

    family.add(person)
    assert person.is_persistent == True
    assert person == family.members[0]


def test_activemethod_persistent_argument(mock_env_client):
    """
    Persistent objects can be sent as activemethod arguments
    """
    api.init()
    family = Family()
    person = Person("Marc", 24)
    family.make_persistent()
    person.make_persistent()
    family.add(person)
    assert person == family.members[0]


def test_activemethod_defined_properties(mock_env_client):
    """
    Object properties defined in class annotations are sychronized between the client and backend
    """
    api.init()
    person = Person("Marc", 24)
    assert person.age == 24

    person.make_persistent()
    person.add_year()
    assert person.age == 25


def test_activemethod_non_defined_properties(mock_env_client):
    """
    Object properties not defined in class annotations are not synchronized between the client and backend
    """
    api.init()
    dog = Dog("Duna", 6)
    assert dog.age == 6

    dog.make_persistent()
    dog.add_year()
    assert dog.age == 6  # Age property is not synchronized
    assert dog.get_age() == 7
