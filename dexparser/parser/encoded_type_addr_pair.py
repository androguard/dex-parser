from dexparser.parser.try_item import TryItem
from hachoir.field import Bytes, FieldSet, UInt16, UInt32

from dexparser.helper.logging import LOGGER
from .utils import ULeb128


class EncodedTypeAddrPair(FieldSet):
    def createFields(self):
        yield ULeb128(self, "type_idx", "type_idx")
        yield ULeb128(self, "addr", "addr")
