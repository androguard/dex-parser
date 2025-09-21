from hachoir.field import Bytes, FieldSet, UInt32

from dexparser.helper.logging import LOGGER

from .utils import ULeb128


class EncodedMethod(FieldSet):
    def createFields(self):
        yield ULeb128(self, "method_idx_diff", "method_idx_diff")
        yield ULeb128(self, "access_flags", "access_flags")
        yield ULeb128(self, "code_off", "code_off")
