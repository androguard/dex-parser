from hachoir.field import FieldSet, UInt32


class StringIdItem(FieldSet):
    def createFields(self):
        yield UInt32(self, "string_data_off", "string_data_off")
