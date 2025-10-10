from dexparser.parser.try_item import TryItem
from hachoir.field import Bytes, FieldSet, UInt16, UInt32

from dexparser.helper.logging import LOGGER
from dexparser.parser.try_item import TryItem
from .utils import SLeb128


class EncodedCatchHandler(FieldSet):
    yield SLeb128(self, "size", "size")
