import pytest

from dataclay.contrib.modeltest.family import Dog, Family, Person


def test_self_is_not_unloaded(client):
    """Test a simple make_persistent call"""
    family = Family()
    family.make_persistent()
    family.test_self_is_not_unloaded()


def test_reference_is_unloaded(client):
    """Test a simple make_persistent call"""
    family = Family()
    family.make_persistent()
    family.test_reference_is_unloaded()
