from hachoir.field import FieldSet, UInt16, UInt32


class FieldIdItem(FieldSet):
    def createFields(self):
        yield UInt16(self, "class_idx", "class_idx")
        yield UInt16(self, "type_idx", "type_idx")
        yield UInt32(self, "name_idx", "name_idx")
