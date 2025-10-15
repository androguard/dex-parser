from hachoir.field import FieldSet

from .utils import ULeb128


class EncodedField(FieldSet):
    def createFields(self):
        yield ULeb128(self, "field_idx_diff", "field_idx_diff")
        yield ULeb128(self, "access_flags", "access_flags")
