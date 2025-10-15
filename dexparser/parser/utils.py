from hachoir.core.endian import LITTLE_ENDIAN
from hachoir.field import Bits

from dexparser.helper.logging import LOGGER


class ULeb128(Bits):
    def __init__(self, parent, name, description=None):
        Bits.__init__(self, parent, name, 8, description)

        size = 8
        value = self._parent.stream.readBits(
            self.absolute_address, 8, LITTLE_ENDIAN
        )

        if value > 0x7F:
            cur = self._parent.stream.readBits(
                self.absolute_address + 8, 8, LITTLE_ENDIAN
            )
            value = (value & 0x7F) | ((cur & 0x7F) << 7)
            size += 8
            if cur > 0x7F:
                cur = self._parent.stream.readBits(
                    self.absolute_address + 16, 8, LITTLE_ENDIAN
                )
                value |= (cur & 0x7F) << 14
                size += 8
                if cur > 0x7F:
                    cur = self._parent.stream.readBits(
                        self.absolute_address + 24, 8, LITTLE_ENDIAN
                    )
                    value |= (cur & 0x7F) << 21
                    size += 8
                    if cur > 0x7F:
                        cur = self._parent.stream.readBits(
                            self.absolute_address + 32, 8, LITTLE_ENDIAN
                        )
                        size += 8
                        if cur > 0x7F:
                            LOGGER.warning("Invalid uleb128")

                    value |= cur << 28

        self._size = size
        self._value = value

    def createValue(self):
        return self._value


class SLeb128(Bits):
    def __init__(self, parent, name, description=None):
        Bits.__init__(self, parent, name, 8, description)

        result = 0
        shift = 0
        size = 0

        for x in range(0, 5):
            value = self._parent.stream.readBits(
                self.absolute_address + 8 * x, 8, LITTLE_ENDIAN
            )
            result |= (value & 0x7F) << shift
            shift += 7
            size += 8

            if not value & 0x80:
                bit_left = max(32 - shift, 0)
                result = result << bit_left
                if result > 0x7FFFFFFF:
                    result = (0x7FFFFFFF & result) - 0x80000000
                result = result >> bit_left
                break

        self._size = size
        self._value = result

    def createValue(self):
        return self._value
