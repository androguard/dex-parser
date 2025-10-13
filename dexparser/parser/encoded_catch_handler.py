from dexparser.parser.try_item import TryItem
from hachoir.field import Bytes, FieldSet, UInt16, UInt32

from dexparser.helper.logging import LOGGER
from dexparser.parser.encoded_type_addr_pair import EncodedTypeAddrPair
from .utils import SLeb128, ULeb128


class EncodedCatchHandler(FieldSet):
    def createFields(self):
        yield SLeb128(self, "size", "size")

        for _ in range(abs(self["size"].value)):
            yield EncodedTypeAddrPair(self, "handlers[]")

        if self["size"].value <= 0:
            yield ULeb128(self, "catch_all_addr", "catch_all_addr")
