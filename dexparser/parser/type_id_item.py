from hachoir.field import FieldSet, UInt32


class TypeIdItem(FieldSet):
    def createFields(self):
        yield UInt32(self, "descriptor_idx", "descriptor_idx")
