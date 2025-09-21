from hachoir.field import Bytes, FieldSet, UInt16, UInt32

from dexparser.helper.logging import LOGGER


class MethodIdItem(FieldSet):
    def createFields(self):
        yield UInt16(self, "class_idx", "class_idx")
        yield UInt16(self, "proto_idx", "proto_idx")
        yield UInt32(self, "name_idx", "name_idx")
