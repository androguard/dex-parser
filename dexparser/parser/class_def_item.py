from hachoir.field import FieldSet, UInt32


class ClassDefItem(FieldSet):
    def createFields(self):
        yield UInt32(self, "class_idx", "class_idx")
        yield UInt32(self, "access_flags", "access_flags")
        yield UInt32(self, "superclass_idx", "superclass_idx")
        yield UInt32(self, "interfaces_off", "interfaces_off")
        yield UInt32(self, "source_file_idx", "source_file_idx")
        yield UInt32(self, "annotations_off", "annotations_off")
        yield UInt32(self, "class_data_off", "class_data_off")
        yield UInt32(self, "static_values_off", "static_values_off")
