from hachoir.field import FieldSet, UInt32


class ProtoIdItem(FieldSet):
    def createFields(self):
        yield UInt32(self, "shorty_idx", "shorty_idx")
        yield UInt32(self, "return_type_idx", "return_type_idx")
        yield UInt32(self, "parameters_off", "parameters_off")
