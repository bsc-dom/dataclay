
""" Class description goes here. """

from uuid import UUID
from yaml import Loader, Dumper

JAVA_UUID_TAG = u'tag:yaml.org,2002:java.util.UUID'
DATACLAY_ID_PREFIX = u'tag:yaml.org,2002:dataclay.util.ids'


def uuid_representer(dumper, data):
    return dumper.represent_scalar(JAVA_UUID_TAG, str(data))


def uuid_constructor(loader, node):
    value = loader.construct_scalar(node)
    return UUID(value)


Dumper.add_representer(UUID, uuid_representer)
Loader.add_constructor(JAVA_UUID_TAG, uuid_constructor)
Loader.add_multi_constructor(
    DATACLAY_ID_PREFIX,
    # This ignores the tag, as ImplementationID, OperationID, *ID are always
    # used directly as their UUID, not their specific type.
    lambda loader, _, node: uuid_constructor(loader, node))
