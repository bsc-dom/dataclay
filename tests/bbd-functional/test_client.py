from pytest_bdd import scenario, given, when, then, parsers
from dataclay import api

# from model.company import Company, Person
import pytest

from steps.make_persistent import *
from steps.common import *


@scenario("../../features/make_persistent.feature", "run a simple make persistent")
def test_make_persistent():
    pass
