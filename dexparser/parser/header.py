from hachoir.field import Bytes, FieldSet, UInt32

from dexparser.helper.logging import LOGGER


class HeaderItem(FieldSet):
    """
    This class can parse an `header_item` of a dex file.
    Several checks are performed to detect if this is not an `header_item`.
    Also the Adler32 checksum of the file is calculated in order to detect file
    corruption.
    """

    def createFields(self):
        yield Bytes(self, "magic", 8, r'DEX signature ("dex\n")')
        yield UInt32(self, "checksum", 'checksum')
        yield Bytes(self, "signature", 20, r'signature)')
        yield UInt32(self, "file_size", 'file_size')
        yield UInt32(self, "header_size", 'header_size')
        yield UInt32(self, "endian_tag", 'endian_tag')
        yield UInt32(self, "link_size", 'link_size')
        yield UInt32(self, "link_off", 'link_off')
        yield UInt32(self, "map_off", 'map_off')
        yield UInt32(self, "string_ids_size", 'string_ids_size')
        yield UInt32(self, "string_ids_off", 'string_ids_off')
        yield UInt32(self, "type_ids_size", 'type_ids_size')
        yield UInt32(self, "type_ids_off", 'type_ids_off')
        yield UInt32(self, "proto_ids_size", 'proto_ids_size')
        yield UInt32(self, "proto_ids_off", 'proto_ids_off')
        yield UInt32(self, "field_ids_size", 'field_ids_size')
        yield UInt32(self, "field_ids_off", 'field_ids_off')
        yield UInt32(self, "method_ids_size", 'method_ids_size')
        yield UInt32(self, "method_ids_off", 'method_ids_off')
        yield UInt32(self, "class_defs_size", 'class_defs_size')
        yield UInt32(self, "class_defs_off", 'class_defs_off')
        yield UInt32(self, "data_size", 'data_size')
        yield UInt32(self, "data_off", 'data_off')

    def isValid(self):
        LOGGER.info("Header isValid")
        if self["endian_tag"].value != 0x12345678:
            return "DEX file with byte swapped endian tag is not supported!"
        return ""
