"""
dataClay includes support for non-volatile memory and in-memory processing.

If you want to manually set up the placement of data you can implement it
within active methods and the data model implementation. However, dataClay 
ships the :class:`InNVM` annotation; this offers a transparent and automatic
in-NVM placement for class attributes.
"""

from dataclay.annotated import PropertyTransformer

try:
    import npp2nvm
except ImportError:
    import warnings

    warnings.warn(
        "npp2nvm package is not installed. InNVM annotation will fail. Install npp2nvm package."
    )
except KeyError:
    import warnings

    warnings.warn(
        "npp2nvm had a configuration error. InNVM annotation will fail. Check npp2nvm documentation."
    )


class InNVM(PropertyTransformer):
    """Store a object attribute in non-volatile memory.

    Attributes annotated with this will be stored and persisted to NVM
    transparently.

    Usage (class definition)::

        class Experiment(DataClayObject):
            observations: Annotated[numpy.ndarray, InNVM()]

    Example::

        >>> e = Experiment()
        >>> e.make_persistent()
        >>> e.observations = np.array([1,2,3])
    """

    def setter(self, value):
        return npp2nvm.np_persist(value)
