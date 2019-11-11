""" Class description goes here. """

import logging
import re
import six
import traceback
if six.PY2:
    import cPickle as pickle
elif six.PY3:
    import _pickle as pickle
    
from dataclay.commonruntime.Initializer import size_tracking
from dataclay.serialization.python.DataClayPythonWrapper import DataClayPythonWrapper
from dataclay.serialization.python.lang.BooleanWrapper import BooleanWrapper
from dataclay.serialization.python.lang.IntegerWrapper import IntegerWrapper
from dataclay.serialization.python.lang.StringWrapper import StringWrapper

import six

logger = logging.getLogger(__name__)

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


def safe_wait_if_compss_future(potential_future):
    """Safe approach to COMPSs Futures: compss_wait_on if that is a Future.

    COMPSs may use Future objects, and this function returns the real object
    (after a call to compss_wait_on to the COMPSs API). If the objects was not
    a Future, return the object itself.

    :param potential_future: May be a PyCOMPSs Future instance
    :return: NOT a Future instance. Redirect potential_future
    """
    real_type = type(potential_future)

    if real_type.__name__ == "Future" and \
            real_type.__module__ == "pycompss.runtime.binding":
        from pycompss.api.api import compss_wait_on

        logger.info("Received a `Future` PyCOMPSs object, waiting for the real object...")
        param = compss_wait_on(potential_future)
        real_type = type(param)
        logger.info("Using the parameter: %r (type: %s)",
                    param, real_type)
    else:
        param = potential_future

    return param


class PyTypeWildcardWrapper(DataClayPythonWrapper):
    """Generic catch-all for Python types (including custom-signature binary types)."""
    __slots__ = ("_signature", "_pickle_fallback")

    PYTHON_PREFIX = 'python.'

    # Note that this regex does not have guarantees on matching <> or [] (so <] will be a valid group,
    # as so will be its [> counterpart). But... that seems a user problem.
    # Also: deep and esoteric nesting is not supported (regex should be thrown away and a sane
    # markup reader used instead).
    SEQUENCE_REGEX = re.compile(r'(?P<base_type>(list)|(tuple)|(set))\s*(?:[<\[]\s*(?P<subtype>.*?)\s*[>\]])?\s*$')
    MAPPING_REGEX = re.compile(r'(?P<base_type>dict)\s*(?:[<\[]\s*(?P<keytype>.*?)\s*,\s*(?P<valuetype>.*?)\s*[>\]])?\s*$')
    STR_SIGNATURE = 'str'
    UNICODE_SIGNATURE = 'unicode'
    STORAGEOBJECT_SIGNATURE = 'storageobject'
    ANYTHING_SIGNATURE = 'anything'
    NUMPY_SIGNATURE = 'numpy'

    def __init__(self, signature, pickle_fallback=False):
        # TODO make some checks, and raise InvalidPythonSignature otherwise
        self._signature = signature
        self._pickle_fallback = pickle_fallback

    def read(self, io_file):
        from dataclay.util.management.classmgr.Utils import serialization_types
        try:
            return serialization_types[self._signature].read(io_file)
        except KeyError:
            pass

        # numpy have their own special ultra-fast serialization
        if self._signature.startswith(self.NUMPY_SIGNATURE):
            import numpy as np
            # Ignoring field size, as numpy is selfcontained in that matter
            _ = IntegerWrapper(32).read(io_file)
            return np.load(io_file, allow_pickle=False)

        # anything is also a special case, also all its alias
        if self._signature == self.ANYTHING_SIGNATURE or \
                self._signature == self.STORAGEOBJECT_SIGNATURE:
            field_size = IntegerWrapper(32).read(io_file)
            logger.debug("Deserializing DataClayObject from pickle")

            return pickle.loads(io_file.read(field_size))

        # Everything shoulda be a python type...
        if not self._signature.startswith(self.PYTHON_PREFIX):
            # ... except the fallbacks (mostly for subtypes like lists of persistent objects)
            # TODO: Check pickle fallback or ignore it completely
            field_size = IntegerWrapper(32).read(io_file)
            return pickle.loads(io_file.read(field_size))

        subtype = self._signature[len(self.PYTHON_PREFIX):]

        sequence_match = self.SEQUENCE_REGEX.match(subtype)
        mapping_match = self.MAPPING_REGEX.match(subtype)

        if sequence_match:
            gd = sequence_match.groupdict()
            logger.debug("Deserializing a Python Sequence with the following match: %s", gd)

            if gd["subtype"]:
                instances_type = PyTypeWildcardWrapper(gd["subtype"], pickle_fallback=True)
            else:  # list without subtypes information
                instances_type = PyTypeWildcardWrapper(self.ANYTHING_SIGNATURE)

            ret = list()
            size = IntegerWrapper(32).read(io_file)
            logger.debug("### READ SIZE OF SEQUENCE MATCH: %i", size)

            for i in range(size):
                if BooleanWrapper().read(io_file):
                    ret.append(instances_type.read(io_file))
                else:
                    ret.append(None)
            
            if gd["base_type"] == "tuple":
                logger.debug("Returning deserialized Python tuple")
                return tuple(ret)
            else:
                logger.debug("Returning deserialized Python list")
                return ret

        elif mapping_match:
            gd = mapping_match.groupdict()
            logger.debug("Deserializing a Python mapping with the following match: %s", gd)

            if gd["keytype"] and gd["valuetype"]:
                key_type = PyTypeWildcardWrapper(gd["keytype"], pickle_fallback=True)
                value_type = PyTypeWildcardWrapper(gd["valuetype"], pickle_fallback=True)
            else:
                # dict without subtypes information
                key_type = PyTypeWildcardWrapper(self.ANYTHING_SIGNATURE)
                value_type = PyTypeWildcardWrapper(self.ANYTHING_SIGNATURE)

            ret = dict()
            size = IntegerWrapper(32).read(io_file)
            for i in range(size):
                if BooleanWrapper().read(io_file):
                    key = key_type.read(io_file)
                else:
                    key = None

                if BooleanWrapper().read(io_file):
                    ret[key] = value_type.read(io_file)
                else:
                    ret[key] = None
            logger.debug("Returning deserialized Python map")
            return ret

        elif subtype == self.STR_SIGNATURE:
            if six.PY2:
                return StringWrapper('binary').read(io_file)
            elif six.PY3:
                return StringWrapper('utf-8').read(io_file)
        elif subtype == self.UNICODE_SIGNATURE:
            return StringWrapper('utf-16').read(io_file)
        else:
            raise NotImplementedError("Python types supported at the moment: "
                                      "list and mappings (but not `%s`), sorry" % subtype)

    def write(self, io_file, value):
        value = safe_wait_if_compss_future(value)

        from dataclay.util.management.classmgr.Utils import serialization_types
        try:
            serialization_types[self._signature].write(io_file, value)
            return
        except KeyError:
            pass

        # numpy have their own special ultra-fast serialization
        if self._signature.startswith(self.NUMPY_SIGNATURE):
            import numpy as np
            with size_tracking(io_file):
                np.save(io_file, value)
            return

        # anything is also a special case, also all its alias
        if self._signature == self.ANYTHING_SIGNATURE or \
                self._signature == self.STORAGEOBJECT_SIGNATURE:
            s = pickle.dumps(value, protocol=-1)
            IntegerWrapper(32).write(io_file, len(s))
            io_file.write(s)
            return

        # Everything shoulda be a python type...
        if not self._signature.startswith(self.PYTHON_PREFIX):
            # ... except the fallbacks (mostly for subtypes like lists of persistent objects)
            # TODO: Check pickle fallback or ignore it completely

            s = pickle.dumps(value, protocol=-1)
            IntegerWrapper(32).write(io_file, len(s))
            io_file.write(s)
            return

        # Now everything must be a python type
        assert self._signature.startswith(self.PYTHON_PREFIX), \
            "Signature for Python types is expected to start with " \
            "'python'. Found signature: %s" % self._signature

        subtype = self._signature[len(self.PYTHON_PREFIX):]

        sequence_match = self.SEQUENCE_REGEX.match(subtype)
        mapping_match = self.MAPPING_REGEX.match(subtype)

        if sequence_match:
            gd = sequence_match.groupdict()
            logger.debug("Serializing a Python Sequence with the following match: %s", gd)

            if gd["subtype"]:
                instances_type = PyTypeWildcardWrapper(gd["subtype"], pickle_fallback=True)
            else:  # list without subtypes information
                instances_type = PyTypeWildcardWrapper(self.ANYTHING_SIGNATURE)

            IntegerWrapper(32).write(io_file, len(value))
            for elem in value:
                if elem is None:
                    BooleanWrapper().write(io_file, False)
                else:
                    BooleanWrapper().write(io_file, True)
                    instances_type.write(io_file, elem)

        elif mapping_match:
            gd = mapping_match.groupdict()
            logger.debug("Serializing a Python Mapping with the following match: %s", gd)

            if gd["keytype"] and gd["valuetype"]:
                key_type = PyTypeWildcardWrapper(gd["keytype"], pickle_fallback=True)
                value_type = PyTypeWildcardWrapper(gd["valuetype"], pickle_fallback=True)
            else:  # dict without subtypes information
                key_type = PyTypeWildcardWrapper(self.ANYTHING_SIGNATURE)
                value_type = PyTypeWildcardWrapper(self.ANYTHING_SIGNATURE)

            IntegerWrapper(32).write(io_file, len(value))

            for k, v in value.items():
                if k is None:
                    BooleanWrapper().write(io_file, False)
                else:
                    BooleanWrapper().write(io_file, True)
                    key_type.write(io_file, k)

                if v is None:
                    BooleanWrapper().write(io_file, False)
                else:
                    # ToDo remove this when COMPSs behaves correctly with compss_wait_on(dict_instance)
                    v = safe_wait_if_compss_future(v)

                    BooleanWrapper().write(io_file, True)
                    value_type.write(io_file, v)

        elif subtype == self.STR_SIGNATURE:
            if six.PY2:
                StringWrapper('utf-8').write(io_file, value)
            elif six.PY3:
                StringWrapper('binary').write(io_file, value)
        elif subtype == self.UNICODE_SIGNATURE:
            StringWrapper('utf-16').write(io_file, value)
        else:
            raise NotImplementedError("Python types supported at the moment: "
                                      "list and mappings (but not `%s`), sorry" % subtype)

