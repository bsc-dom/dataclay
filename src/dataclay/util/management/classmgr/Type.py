
""" Class description goes here. """

from dataclay.util.MgrObject import ManagementObject

   
# Added descriptor and typeName
class Type(ManagementObject):
    _fields = ["id",  # sql id, internals
               "descriptor",
               "signature",
               "typeName",
               "includes",
               ]

    _internal_fields = ["languageDepInfos",
                        ]

    @staticmethod
    def build_from_type(type_instance):
        """Build a Type from a type instance (of a decorator, typically).
        :param type_instance: The instance passed to the decorator. Note that
        this may be a real type (like int, str, a custom DataClayObject class...)
        or it may be a string like 'list<storageobject>'.
        :return: A Type instance.
        """
        
        # Imports done here to avoid circular-imports during initialization
        from dataclay.util.management.classmgr.Utils import instance_types
        from dataclay import DataClayObject
        try:
            return instance_types[type_instance]
        except KeyError:
            pass
        if isinstance(type_instance, str):
            return Type.build_from_docstring(type_instance)
        elif issubclass(type_instance, DataClayObject):
            full_name = type_instance.get_class_extradata().full_name
            namespace = type_instance.get_class_extradata().namespace
            # TODO: Check UserType fields
            from dataclay.util.management.classmgr.UserType import UserType  # Import after creation to avoid circular imports
            return UserType(namespace=namespace,
                            typeName=full_name,
                            signature=("L%s;" % full_name).replace(".", "/"),
                            includes=[])
        else:
            raise RuntimeError("Using a type instance is only supported for "
                               "language primitives and DataClayObjects")

    @staticmethod
    def build_from_docstring(type_str):
        
        """Build a Type from the docstring name.
        :param type_str: The string the registrator used for that Type.
        :return: A Type instance.

        This function recognizes the different kinds of types the user can use
        like 'int', 'float' for Python-native primitive types, 'list<...>'
        for Python-specific types or full class names for registered classes.
        """
        
        # Imports done here to avoid circular-imports during initialization
        from dataclay.util.management.classmgr.Utils import NATIVE_PACKAGES, docstring_types
        try:
            return docstring_types[type_str]
        except KeyError:
            pass

        if type_str.startswith("list") or \
           type_str.startswith("tuple") or \
           type_str.startswith("set") or \
           type_str.startswith("dict") or \
           type_str == "str":
            # In Python we decided (COMPSs + Hecuba + dataClay) to use basic_type<sub_type>
            # but not sure whereelse is expecting basic_type[sub_type]... but maybe
            # [] notation is only used for array-based containers. Proceed with caution!
            return Type(signature="python.%s" % type_str.replace("<", "[").replace(">", "]"),
                        includes=[])

        elif type_str == "anything" or type_str == "storageobject":
            return Type(signature=type_str,
                        includes=[])
        else:
            try:
                namespace, full_name = type_str.split('.', 1)
            except ValueError:
                raise ValueError("Could not split namespace and full_name from %s" % type_str)

            if namespace in NATIVE_PACKAGES:
                return Type(signature=type_str,
                            includes=[])
            else:
                from dataclay.util.management.classmgr.UserType import UserType  # Import after creation to avoid circular imports
                return UserType(namespace=namespace,
                                typeName=full_name,
                                signature=("L%s;" % full_name).replace(".", "/"),
                                includes=[])

