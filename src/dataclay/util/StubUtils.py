
""" Class description goes here. """

from dataclay.communication.grpc.messages.common.common_messages_pb2 import LANG_PYTHON
import logging
import os

from dataclay.commonruntime.Runtime import getRuntime
from dataclay.commonruntime.Settings import settings
from dataclay.util.FileUtils import deploy_class
from dataclay.util.YamlParser import Loader, dataclay_yaml_load

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

_babel_data = None
logger = logging.getLogger(__name__)


def babel_stubs_load(stream):
    # Note the explicit list, just in case the caller wants to close the provided file/buffer
    map_babel_stubs = dataclay_yaml_load(stream, Loader=Loader)
    result = list()
    for k, v in map_babel_stubs.items():
        result.append(dataclay_yaml_load(v))
    return result


def prepare_storage(stubs_folder=None):
    """Ensure (force creation if not exists) the STUB_STORAGE folder.

    By default, the settings.stubs_folder is used. You can override by providing
    the stubs_folder argument.
    """
    if not stubs_folder:
        stubs_folder = settings.stubs_folder

    if not os.path.exists(stubs_folder):
        os.mkdir(stubs_folder)

    if not os.path.isdir(stubs_folder):
        raise IOError("The `StubsClasspath` is not a folder --check file and permissions")


def load_babel_data(stubs_folder=None):
    """Load all Babel Stub data from the cached file.

    By default, the settings.stubs_folder is used. You can override by providing
    the stubs_folder argument.

    :return: A dictionary (the parsed YAML).
    """
    global _babel_data
    if _babel_data is None:
        with open(os.path.join(stubs_folder or settings.stubs_folder,
                               "babelstubs.yml"),
                  'rb') as f:
            _babel_data = babel_stubs_load(f)

    return _babel_data


def deploy_stubs(stubs_folder=None):
    """Perform the actual deployment of classes (python files).

    By default, the settings.stubs_folder is used. You can override by providing
    the stubs_folder argument.
    """
    if not stubs_folder:
        stubs_folder = settings.stubs_folder

    # Use the stored StubInfo (which is a YAML)
    babel_data = load_babel_data(stubs_folder)
    source_deploy = os.path.join(stubs_folder, 'sources')
    try:
        os.makedirs(source_deploy)
    except OSError as e:
        if e.errno != 17:
            # Not the "File exists" expected error, reraise it
            raise

    for class_data in babel_data:
        namespace = class_data.namespace
        full_name = class_data.className

        logger.debug("Deploying stub for %s::%s", namespace, full_name)
    
        try:
            # ToDo: to avoid clashes, in the future, maybe the full name should include the namespace
            # like: ... stubs_folder, "%s.%s" % (namespace, full_name ...
            with open(os.path.join(stubs_folder, full_name), 'rt') as f:
                source = f.read()
        except IOError:
            source = ""
    
        deploy_class(namespace, full_name, source, u"", source_deploy)


def track_local_available_classes():
    """Track the available classes into the commonruntime.local_available_classes.

    Note that no deployment is done in this function: the deployment should be
    done beforehand through the deploy_stubs function.

    This function returns all the contracts that have been found.
    """
    babel_data = load_babel_data()
    contracts = set()

    for class_data in babel_data:
        contracts.update(class_data.contracts)
        namespace = class_data.namespace
        full_name = class_data.className

        getRuntime().local_available_classes[class_data.classID] = \
            "%s.%s" % (namespace, full_name)

    logger.verbose("Using the following contracts: %s", contracts)
    return contracts
