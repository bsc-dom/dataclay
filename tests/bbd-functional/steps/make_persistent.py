from pytest_bdd import scenario, scenarios, given, when, then, parsers
from dataclay import api

# from model.company import Company, Person
import pytest

# scenarios("../../features")


@when("call make_persistent")
@when(parsers.parse("call make_persistent to '{obj_name}'"))
def make_persistent(context, dc_object, obj_name=None):
    if obj_name is not None:
        context[obj_name].make_persistent()
    else:
        dc_object.make_persistent()


@then("Is persistent")
@then("'{obj_name}' is persistent")
def check_is_persistent(context, dc_object, obj_name=None):
    if obj_name is not None:
        assert context[obj_name]._dc_is_persistent == True
    else:
        assert dc_object._dc_is_persistent == True
