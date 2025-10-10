from dexparser.parser.try_item import TryItem
from hachoir.field import Bytes, FieldSet, UInt16, UInt32

from dexparser.helper.logging import LOGGER
from dexparser.parser.try_item import TryItem
from .utils import ULeb128


class CodeItem(FieldSet):
    def createFields(self):
        yield UInt16(self, "registers_size", 'registers_size')
        yield UInt16(self, "ins_size", 'ins_size')
        yield UInt16(self, "outs_size", 'outs_size')
        yield UInt16(self, "tries_size", 'tries_size')
        yield UInt32(self, "debug_info_off", 'debug_info_off')
        yield UInt32(self, "insns_size", 'insns_size')

        print(self["registers_size"].value, self["ins_size"].value, self["outs_size"].value, self["tries_size"].value, self["debug_info_off"].value, self["insns_size"].value)


        yield UInt16(self, "insns[]", self["insns_size"].value)

        # Instructions buffer
        #yield Bytes(self, "insns", self["insns_size"].value*2, r'insns')
        
        # TyItem data
        if self["tries_size"].value > 0:
            for index in range(self["tries_size"].value):
                yield TryItem(self, "try_item[]")

            yield ULeb128(self, "encoded_catch_handler_list_size", "encoded_catch_handler_list_size")
            print("encoded_catch_handler_list_size", self["encoded_catch_handler_list_size"].value)
        