from hachoir.field import Bytes, FieldSet, UInt32

from dexparser.helper.logging import LOGGER

from .encoded_field import EncodedField
from .encoded_method import EncodedMethod
from .utils import ULeb128


class ClassDataItem(FieldSet):
    def createFields(self):
        yield ULeb128(self, "static_fields_size", "static_fields_size")
        yield ULeb128(self, "instance_fields_size", "instance_fields_size")
        yield ULeb128(self, "direct_methods_size", "direct_methods_size")
        yield ULeb128(self, "virtual_methods_size", "virtual_methods_size")

        for _ in range(self["static_fields_size"].value):
            yield EncodedField(self, "static_fields[]")

        for _ in range(self["instance_fields_size"].value):
            yield EncodedField(self, "instance_fields[]")

        for _ in range(self["direct_methods_size"].value):
            yield EncodedMethod(self, "direct_methods[]")

        for _ in range(self["virtual_methods_size"].value):
            yield EncodedMethod(self, "virtual_methods[]")
