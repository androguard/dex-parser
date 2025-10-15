from hachoir.field import FieldSet, String

from .utils import ULeb128


class StringDataItem(FieldSet):
    def createFields(self):
        yield ULeb128(self, "utf16_size_uleb", "utf16_size_uleb")
        if self["utf16_size_uleb"].value > 0:
            yield String(self, "data", self["utf16_size_uleb"].value, "data")
