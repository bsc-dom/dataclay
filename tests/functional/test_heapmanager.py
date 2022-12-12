from dataclay import api
import pytest
from model.family import Family, Person, Dog
from utils import init_client, mock_env_client


def test_retain_and_flush(init_client):
    """Test a simple make_persistent call"""
    # api.init()
    family = Family()
    family.make_persistent()
    family.test_retain_and_flush()
