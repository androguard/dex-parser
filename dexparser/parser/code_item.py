from hachoir.field import Bytes, FieldSet, UInt16, UInt32

from dexparser.helper.logging import LOGGER


class CodeItem(FieldSet):
    def createFields(self):
        yield UInt16(self, "registers_size", 'registers_size')
        yield UInt16(self, "ins_size", 'ins_size')
        yield UInt16(self, "outs_size", 'outs_size')
        yield UInt16(self, "tries_size", 'tries_size')
        yield UInt32(self, "debug_info_off", 'debug_info_off')
        yield UInt32(self, "insns_size", 'insns_size')
