import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person

# def test_dc_put(client):
#     person = Person("Marc", 24)
#     person.dc_put("test_dc_put")
#     assert person._dc_is_registered == True
#     assert person.name == "Marc"
#     assert person.age == 24
#     Person.delete_alias("test_dc_put")


# def test_dc_clone(client):
#     person = Person("Marc", 24)
#     person.dc_put("test_dc_clone")
#     copy = person.dc_clone()
#     assert copy.name == person.name
#     assert copy.age == person.age
#     Person.delete_alias("test_dc_clone")


# def test_dc_clone_by_alias(client):
#     person = Person("Marc", 24)
#     person.dc_put("test_dc_clone_by_alias")
#     clone = Person.dc_clone_by_alias("test_dc_clone_by_alias")
#     assert clone.name == person.name
#     assert clone.age == person.age
#     Person.delete_alias("test_dc_clone_by_alias")


# def test_dc_update(client):
#     person = Person("Marc", 24)
#     person.dc_put("test_dc_update")
#     new_person = Person("Alice", 32)
#     person.dc_update(new_person)
#     assert person.name == new_person.name
#     assert person.age == new_person.age
#     Person.delete_alias("test_dc_update")


# def test_dc_update_by_alias(client):
#     person = Person("Marc", 24)
#     person.dc_put("test_dc_update_by_alias")
#     new_person = Person("Alice", 32)
#     Person.dc_update_by_alias("test_dc_update_by_alias", new_person)
#     assert person.name == new_person.name
#     assert person.age == new_person.age
#     Person.delete_alias("test_dc_update_by_alias")


# def test_dc_set(client):
#     person = Person("Marc", 24)
#     person.dc_put("test_dc_set")
#     person.name = "David"
#     assert person.name == "David"
#     Person.delete_alias("test_dc_set")
