from hachoir.field import Bytes, FieldSet, UInt32

from dexparser.helper.logging import LOGGER


class StringIdItem(FieldSet):
    def createFields(self):
        yield UInt32(self, "string_data_off", "string_data_off")
