from hachoir.field import Bits, Bytes, FieldError, FieldSet, String, UInt8, UInt32

from dexparser.helper.logging import LOGGER

from .utils import ULeb128


class StringDataItem(FieldSet):
    def createFields(self):
        yield ULeb128(self, "utf16_size_uleb", "utf16_size_uleb")
        if self["utf16_size_uleb"].value > 0:
            yield String(self, "data", self["utf16_size_uleb"].value, "data")
