"""Custom container for holding extra information on classes.

The dataClay friendly classed (either before registration or stub-generated
ones) will contain their extra information --like the full_name, the class_id
or the namespace-- in DataClayExtraData instances.
"""

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'


class DataClayCommonExtraData(object):
    """ExtraData commonlib base class.

    ExtraData behaves as a dictionary, with some optional extras.
    """
    __slots__ = list()

    def __init__(self, **kwargs):
        # load values into slots
        for k, v in kwargs.items():
            # Let the errors trigger from here (if kwargs is invalid)
            setattr(self, k, v)

        # force None (to avoid attribute errors)
        for s in self.__slots__:
            try:
                _ = getattr(self, s)
            except AttributeError:
                setattr(self, s, None)

    def __str__(self):
        ret = ["{%s contents:" % self.__class__.__name__, ]

        for s in self.__slots__:
            ret.append("  %s: %s" % (s, getattr(self, s)))
        ret.append("}")

        return "\n".join(ret)


class DataClayClassExtraData(DataClayCommonExtraData):
    """Container for ExtraData related to a certain dataClay Class

    Instances for this class are typically associated to DataClayObject
    derived classes (and automatically populated by the ExecutionGateway).
    """
    __slots__ = ('full_name',
                 'namespace',
                 'classname',
                 'class_id',
                 'properties',
                 'imports',
                 'stub_info',
                 'metaclass_container',
                 )


class DataClayInstanceExtraData(DataClayCommonExtraData):
    """Container for ExtraData related to a certain dataClay Object instance.

    Instances for this class are typically created and assigned to a certain
    DataClayObject instance when creating them. The ExecutionGateway populates
    its data.
    """
    __slots__ = ('persistent_flag',
                 'object_id',
                 'master_location',
                 'dataset_id',
                 'execenv_id',
                 'loaded_flag',
                 'pending_to_register_flag',
                 'owner_session_id',
                 'dirty_flag',
                 'memory_pinned',
                 )
