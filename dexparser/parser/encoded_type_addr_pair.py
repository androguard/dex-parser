from hachoir.field import FieldSet

from .utils import ULeb128


class EncodedTypeAddrPair(FieldSet):
    def createFields(self):
        yield ULeb128(self, "type_idx", "type_idx")
        yield ULeb128(self, "addr", "addr")
