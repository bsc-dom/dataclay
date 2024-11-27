from datetime import datetime

import pytest

from dataclay import AlienDataClayObject, DataClayObject
from dataclay.contrib.modeltest.alien import Dog, Person


def test_alien_builtin(client):
    """Test a simple make_persistent on a builtin type"""
    l = AlienDataClayObject([1, 2, 3])

    assert isinstance(l, AlienDataClayObject)
    assert isinstance(l, DataClayObject)

    l.make_persistent()

    assert l._dc_is_registered is True
    assert len(l) == 3
    assert l.__len__() == 3

    l.append(4)
    assert len(l) == 4


def test_alien_proxy_classes(client):
    d = AlienDataClayObject({"a": 1, "b": 2})
    d_bis = AlienDataClayObject({"a": 1, "b": 2})

    d.make_persistent()
    d_bis.make_persistent()

    assert type(d) is type(d_bis)


def test_alien_python_class(client):
    now = datetime.now()

    persistent_now = AlienDataClayObject(now)
    persistent_now.make_persistent()

    assert persistent_now == now
    assert now == persistent_now

    assert persistent_now._dc_is_registered is True


def test_alien_pydantic_model(client):
    p = AlienDataClayObject(Person(name="Alice", age=30))
    p.make_persistent()

    assert p._dc_is_registered is True

    assert p.name == "Alice"
    assert p.age == 30

    assert p.dict() == {"name": "Alice", "age": 30}

    same_person_json = {"name": "Alice", "age": 30}
    same_person = AlienDataClayObject(Person.parse_obj(same_person_json))
    same_person.make_persistent()

    assert same_person.name == p.name
    assert same_person.age == p.age

    p.name = "Bob"
    p.age = 42

    assert same_person.name != p.name
    assert same_person.age != p.age


def test_alien_pydantic_methods(client):
    reference = Person(name="Alice", age=30)

    p = AlienDataClayObject(Person(name="Alice", age=30))
    p.make_persistent()

    assert p.dict() == reference.dict()


def test_alien_getsetdelitem(client):
    p = AlienDataClayObject({"a": 1, "b": 2})

    assert p["a"] == 1
    p["c"] = 3
    with pytest.raises(KeyError):
        p["d"]

    del p["a"]
    with pytest.raises(KeyError):
        p["a"]

    p.make_persistent()
    with pytest.raises(KeyError):
        p["a"]
    assert p["b"] == 2
    p["c"] = 42
    assert p["c"] == 42
    del p["b"]

    assert "a" not in p
    assert "b" not in p


def test_alien_getsetdelattr(client):
    d = AlienDataClayObject(Dog())

    d.name = "Fido"
    d.age = 5
    assert d.age == 5
    del d.age
    with pytest.raises(AttributeError):
        d.age

    d.make_persistent()
    assert d.name == "Fido"
    d.age = 6
    assert d.age == 6

    del d.name
    with pytest.raises(AttributeError):
        d.name
