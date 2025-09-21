from hachoir.field import Bytes, FieldSet, UInt32

from dexparser.helper.logging import LOGGER
from dexparser.parser.map_item import MapItem


class MapList(FieldSet):
    """
    This class can parse the "map_list" of the dex format

    https://source.android.com/devices/tech/dalvik/dex-format#map-list
    """

    def createFields(self):
        yield UInt32(self, "size", "size")
        for index in range(self["size"].value):
            yield MapItem(self, "map_item[]")

    def get_code_item(self):
        for index in range(self["size"].value):
            current_map_item = self["map_item[" + str(index) + "]"]
            if str(current_map_item["type"]) == "CODE_ITEM":
                return current_map_item
        return None

    def get_class_data_item(self):
        for index in range(self["size"].value):
            current_map_item = self["map_item[" + str(index) + "]"]
            if str(current_map_item["type"]) == "CLASS_DATA_ITEM":
                return current_map_item
        return None
