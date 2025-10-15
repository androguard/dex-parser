from hachoir.field import FieldSet, UInt16, UInt32


class TryItem(FieldSet):
    def createFields(self):
        yield UInt32(self, "start_addr", 'start_addr')
        yield UInt16(self, "insn_count", 'insn_count')
        yield UInt16(self, "handler_off", 'handler_off')
