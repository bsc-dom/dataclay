
""" Class description goes here. """

import logging
from yaml import load, dump, Loader, Dumper

from dataclay.commonruntime.Initializer import size_tracking
from dataclay.serialization.DataClaySerializable import DataClaySerializable
from dataclay.serialization.python.lang.StringWrapper import StringWrapper
import six

logger = logging.getLogger(__name__)


class ManagementMetaClass(type):

    def __init__(cls, name, bases, kwds):
        """This overlaps quite a bit with YAMLObjectMetaclass."""
        if name != "ManagementObject":
            yaml_tag = u"tag:yaml.org,2002:es.bsc.%s" % (cls.__module__)
            cls.yaml_loader = Loader
            cls.yaml_tag = yaml_tag  # used by `ManagementObject.to_yaml`
            logger.trace("YAML TAG : %s", yaml_tag)
            Loader.add_constructor(yaml_tag, cls.from_yaml)
            Dumper.add_representer(cls, cls.to_yaml)
        super(ManagementMetaClass, cls).__init__(name, bases, kwds)

    def __new__(cls, name, bases, dct):
        if "_fields" not in dct:
            raise AttributeError("All YAML structures must have a `_fields` list attribute")

        if name == "ManagementObject":
            dct["__slots__"] = tuple()
            return super(ManagementMetaClass, cls).__new__(cls, name, bases, dct)

        # Note that ManagementObject class instantiation cannot reach here,
        # or a cyclic requirement will happen and it will crash

        if ManagementObject not in bases:
            # We are instantiating a derived class, merge all the attributes as expected
            full_fields = list()
            full_internal = list()

            for b in bases:
                if issubclass(b, ManagementObject):
                    # Note that we are not resolving correctly overrides
                    # But we do NOT expect the override on typed fields
                    # (it would be quite pathological)
                    try:
                        dct["_typed_fields"].update(b._typed_fields)
                    except KeyError:
                        pass

                    full_fields += b._fields
                    try:
                        full_internal += b._internal_fields
                    except AttributeError:
                        pass

            full_fields += dct["_fields"]
            if "_internal_fields" in dct:
                full_internal += dct["_internal_fields"]

            # Ensure that the generated class has complete `_fields` and `_internal_fields`
            dct["_fields"] = full_fields
            dct["_internal_fields"] = full_internal
            all_fields = full_fields + full_internal

        else:
            all_fields = list(dct["_fields"])

            if "_internal_fields" in dct:
                all_fields += dct["_internal_fields"]

        dct["__slots__"] = tuple(all_fields)

        return super(ManagementMetaClass, cls).__new__(cls, name, bases, dct)


@six.add_metaclass(ManagementMetaClass)
class ManagementObject(DataClaySerializable):
    _fields = list()
    _internal_fields = list()
    _typed_fields = dict()

    yaml_tag = None

    def __init__(self, **kwargs):
        super(ManagementObject, self).__init__()
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def from_yaml(cls, loader, node):
        """See YAMLObject."""
        return loader.construct_yaml_object(node, cls)

    @classmethod
    def to_yaml(cls, dumper, data):
        """See YAMLObject."""
        return dumper.represent_yaml_object(cls.yaml_tag, data, cls)

    def __getstate__(self):
        """This method is used both by Pickle and by YAML Dumper."""

        # All required fields should be there
        ret = {k: getattr(self, k, None) for k in self._fields}

        # Include all internal fields which are present (even if they are None)
        ret.update({k: getattr(self, k) for k in self._internal_fields
                    if hasattr(self, k)})
        return ret

    def __setstate__(self, state):
        """This method is used both by Pickle and by YAML Loader."""
        setted_attrs = set()
        unsetted_attrs = set()
        for k, v in state.items():
            # TODO: Check better fields

            if isinstance(v, dict) and k in self._typed_fields:
                typed_field = self._typed_fields[k]
                new_attr = typed_field()
                new_attr.__setstate__(v)
                v = new_attr

            try:
                setattr(self, k, v)
                setted_attrs.add(k)
            except Exception:
                unsetted_attrs.add(k)

        missed_fields = set(self._fields) - setted_attrs

        if len(missed_fields) != 0:
            logger.error("WARNING -- __setstate__ on class %s called without this fields: %s" 
            , self.__class__, list(missed_fields))
        if len(unsetted_attrs) > 0:
            logger.error("WARNING -- Attributes %s are not setted -- Fields missing on class %s"
            , unsetted_attrs, self.__class__)

    def __str__(self):
        lines = ["ManagementObject: %s" % self.__class__.__name__]
        for field_name in self._fields:
            try:
                lines.append("  - %s: %r" % (field_name, getattr(self, field_name)))
            except AttributeError:
                logger.debug("WARNING -- Missing attribute: %s", field_name)
                pass

        return "\n".join(lines)

    def serialize(self, io_file):
        """Serialize this instance into a IO like (file, StringIO...)."""
        # This is roughly equivalent to write into a string
        # and perform a Str().write, but with less memory copies
        with size_tracking(io_file):
            dump(self, io_file, encoding='utf-16-be', Dumper=Dumper)

    @classmethod
    def deserialize(cls, io_file):
        """Deserialize the IO into a new instance."""
        value = StringWrapper().read(io_file)
        return load(value, Loader=Loader)

    read = deserialize

    @classmethod
    def write(cls, io_file, value):
        assert isinstance(value, cls), \
            "Called `write` on class '%s' with an object of class '%s'" % (
                cls.__name__, type(value).__name__)
        value.serialize(io_file)

    @staticmethod
    def type_equal(deserialized, orig_val):
        ret_bool = True
        ret_list = []
        try:
            if deserialized.typeName == orig_val.typeName:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("typeName")
            pass
        try:
            if deserialized.languageDepInfos == orig_val.languageDepInfos:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("languageDepInfos")
            pass
        try:
            if deserialized.descriptor == orig_val.descriptor:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("descriptor")
            pass

        try:
            if deserialized.signature == orig_val.signature:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("signature")
            pass
        try:
            if deserialized.includes == orig_val.includes:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("includes")
            pass

        return ret_bool, ret_list

    @staticmethod
    def prop_equal(deserialized, orig_val, i=None):
        ret_bool = True
        ret_list = []
        # for i in range(0, len(orig_val)):
        if i is not None:
            try:
                if deserialized.namespace == orig_val[i].namespace:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append(str(i) + " namespace")

            try:
                if deserialized.className == orig_val[i].className:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append(str(i) + " className")

            try:
                if deserialized.getterImplementationID == orig_val[i].getterImplementationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append(str(i) + " getterImplementationID")

            try:
                if deserialized.setterImplementationID == orig_val[i].setterImplementationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append(str(i) + " setterImplementationID")

            try:
                if deserialized.name == orig_val[i].name:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append(str(i) + " name")

            try:
                if deserialized.position == orig_val[i].position:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append(str(i) + " position")

            try:
                if deserialized.getterOperationID == orig_val[i].getterOperationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append(str(i) + " getterOperationID")

            try:
                if deserialized.setterOperationID == orig_val[i].setterOperationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append(str(i) + " setterOperationID")

            try:
                if deserialized.metaClassID == orig_val[i].metaClassID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append(str(i) + " metaClassID")

            try:
                if deserialized.namespaceID == orig_val[i].namespaceID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append(str(i) + " namespaceID")

            try:
                if deserialized.languageDepInfos == orig_val[i].languageDepInfos:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append(str(i) + " languageDepInfos")
        else:
            # MetaClass_Factory
            try:
                if deserialized.namespace == orig_val.namespace:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append("namespace")

            try:
                if deserialized.className == orig_val.className:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append("className")

            try:
                if deserialized.getterImplementationID == orig_val.getterImplementationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append("getterImplementationID")

            try:
                if deserialized.setterImplementationID == orig_val.setterImplementationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("setterImplementationID")

            try:
                if deserialized.name == orig_val.name:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("name")

            try:
                if deserialized.position == orig_val.position:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("position")

            try:
                if deserialized.getterOperationID == orig_val.getterOperationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("getterOperationID")

            try:
                if deserialized.setterOperationID == orig_val.setterOperationID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("setterOperationID")

            try:
                if deserialized.metaClassID == orig_val.metaClassID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("metaClassID")

            try:
                if deserialized.namespaceID == orig_val.namespaceID:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("namespaceID")

            try:
                if deserialized.languageDepInfos == orig_val.languageDepInfos:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list

            except AttributeError:
                ret_list.append("languageDepInfos")

        return ret_bool, ret_list

    @staticmethod
    def op_equal(deserialized, orig_val, b_par=False):
        ret_bool = True
        ret_list = []
        try:
            if deserialized.namespace == orig_val.namespace:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("namespace")

        try:
            if deserialized.className == orig_val.className:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("className")

        try:
            if deserialized.descriptor == orig_val.descriptor:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("descriptor")

        try:
            if deserialized.signature == orig_val.signature:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("signature")

        try:
            if deserialized.name == orig_val.name:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("name")

        try:
            if deserialized.nameAndDescriptor == orig_val.nameAndDescriptor:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("nameAndDescriptor")
        if b_par:
            # Not executed by Metaclass_Factory
            try:
                if deserialized.params == orig_val.params:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("params")

            try:
                if deserialized.returnType == orig_val.returnType:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("returnType")

            try:
                if deserialized.implementations == orig_val.implementations:
                    ret_bool = True
                else:
                    ret_bool = False
                    return ret_bool, ret_list
            except AttributeError:
                ret_list.append("implementations")

        try:
            if deserialized.paramsOrder == orig_val.paramsOrder:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("paramsOrder")

        try:
            if deserialized.isAbstract == orig_val.isAbstract:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("isAbstract")

        try:
            if deserialized.isStaticConstructor == orig_val.isStaticConstructor:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("isStaticConstructor")

        try:
            if deserialized.metaClassID == orig_val.metaClassID:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("metaClassID")

        try:
            if deserialized.namespaceID == orig_val.namespaceID:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("namespaceID")

        try:
            if deserialized.languageDepInfos == orig_val.languageDepInfos:
                ret_bool = True
            else:
                ret_bool = False
                return ret_bool, ret_list
        except AttributeError:
            ret_list.append("languageDepInfos")

        return ret_bool, ret_list
