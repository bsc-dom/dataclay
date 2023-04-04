import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person


def test_new_version_and_consolidate(client):
    person = Person("Marc", 24)
    person.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    person_v1.consolidate_version()
    assert person.name == "Alice"


def test_version_of_version(client):
    person = Person("Marc", 24)
    person.make_persistent()

    person_v1 = person.new_version()
    person_v1.name = "Alice"
    assert person.name == "Marc"

    person_v2 = person_v1.new_version()
    person_v2.name = "Carol"
    assert person_v1.name == "Alice"

    person_v2.consolidate_version()
    assert person.name == "Carol"
