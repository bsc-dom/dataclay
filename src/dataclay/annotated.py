class PropertyTransformer:
    """Parent class for annotations that transform object attributes.

    This class is not intended to be used by itself, but instead inherited and
    implemented. Right now, this class is a trivial implementation, i.e.
    passthrough of getter and setter.

    When the :method getter: is implemented, it will be used to transform the
    data during ``getattr`` operations.

    Similarly, the :method setter: is used to transform the value during
    ``setattr`` operations.
    """

    def getter(self, value):
        """Transform the value during a ``getattr`` operation."""
        return value

    def setter(self, value):
        """Transform the value during a ``setattr`` operation."""
        return value


class LocalOnly:
    """Annotation to specify attributes that must no be persisted.

    Example::

        class ComplexAlgorithm(DataClayObject):
            primes_cache: Annotated[list[int], LocalOnly]
    """

    pass
