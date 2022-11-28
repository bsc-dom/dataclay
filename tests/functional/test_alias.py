from dataclay import api
from dataclay.exceptions import *

import pytest
from model.family import Family, Person
from utils import init_client, mock_env_client


def test_get_by_alias(init_client):
    person = Person("Marc", 24)
    person.make_persistent(alias="marc")
    assert person == Person.get_by_alias("marc")


def test_delete_alias(init_client):
    person = Person("Marc", 24)
    person.make_persistent("p1")
    Person.delete_alias("p1")
    pytest.raises(DataClayException, Person.get_by_alias, alias="p1")
