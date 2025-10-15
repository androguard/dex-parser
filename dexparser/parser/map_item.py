from hachoir.core.text_handler import hexadecimal, textHandler
from hachoir.field import Enum, FieldSet, UInt16, UInt32


class MapItem(FieldSet):
    """
    Implementation of a map_item, which occours in a map_list

    https://source.android.com/devices/tech/dalvik/dex-format#map-item
    """

    TYPE_NAME = {
        0x0: "HEADER_ITEM",
        0x1: "STRING_ID_ITEM",
        0x2: "TYPE_ID_ITEM",
        0x3: "PROTO_ID_ITEM",
        0x4: "FIELD_ID_ITEM",
        0x5: "METHOD_ID_ITEM",
        0x6: "CLASS_DEF_ITEM",
        0x7: "CALL_SITE_ITEM",  # New in DEX038
        0x8: "METHOD_HANDLE_ITEM",  # New in DEX038
        0x1000: "MAP_LIST",
        0x1001: "TYPE_LIST",
        0x1002: "ANNOTATION_SET_REF_LIST",
        0x1003: "ANNOTATION_SET_ITEM",
        0x2000: "CLASS_DATA_ITEM",
        0x2001: "CODE_ITEM",
        0x2002: "STRING_DATA_ITEM",
        0x2003: "DEBUG_INFO_ITEM",
        0x2004: "ANNOTATION_ITEM",
        0x2005: "ENCODED_ARRAY_ITEM",
        0x2006: "ANNOTATIONS_DIRECTORY_ITEM",
        0xF000: "HIDDENAPI_CLASS_DATA_ITEM",
    }

    def createFields(self):
        yield Enum(
            textHandler(UInt16(self, "type", "Map type"), hexadecimal),
            self.TYPE_NAME,
        )

        yield UInt16(self, "unused", "unused")
        yield UInt32(self, "size", "size")
        yield UInt32(self, "offset", "offset")

    def createDescription(self):
        return "map_item"
