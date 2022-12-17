from dataclay import api
import pytest
from model.family import Family, Person, Dog


def test_self_is_not_unloaded(init_client):
    """Test a simple make_persistent call"""
    # api.init()
    family = Family()
    family.make_persistent()
    family.test_self_is_not_unloaded()


def test_reference_is_unloaded(init_client):
    """Test a simple make_persistent call"""
    # api.init()
    family = Family()
    family.make_persistent()
    family.test_reference_is_unloaded()
