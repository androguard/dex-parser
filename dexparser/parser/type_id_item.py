from hachoir.field import Bytes, FieldSet, UInt32

from dexparser.helper.logging import LOGGER


class TypeIdItem(FieldSet):
    def createFields(self):
        yield UInt32(self, "descriptor_idx", "descriptor_idx")
