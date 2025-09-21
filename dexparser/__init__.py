import io
from typing import Iterator

from hachoir.core.endian import LITTLE_ENDIAN
from hachoir.field import (
    MissingField,
    RootSeekableFieldSet,
)
from hachoir.parser import HachoirParser
from hachoir.stream import StringInputStream

from dexparser.helper.logging import LOGGER
from dexparser.parser import constants
from dexparser.parser.class_data_item import ClassDataItem
from dexparser.parser.class_def_item import ClassDefItem
from dexparser.parser.code_item import CodeItem
from dexparser.parser.header import HeaderItem
from dexparser.parser.map_list import MapList
from dexparser.parser.method_id_item import MethodIdItem
from dexparser.parser.proto_id_item import ProtoIdItem
from dexparser.parser.string_data_item import StringDataItem
from dexparser.parser.string_id_item import StringIdItem
from dexparser.parser.type_id_item import TypeIdItem

class DEX(HachoirParser, RootSeekableFieldSet):
    """
    This class can parse a classes.dex file of an Android application (APK).

    :param buff: a string which represents the classes.dex file
    :param decompiler: associate a decompiler object to display the java source code

    Example:

        >>> d = DEX( filestream("classes.dex") )
    """

    PARSER_TAGS = {
        "id": "dex",
        "category": "program",
        "file_ext": ("dex", "dey", ""),
        "min_size": 112,  # At least one DEX header ?
        "mime": ("application/x-dex"),
        "magic": (
            (constants.DEX_FILE_MAGIC_35, 0),
            (constants.DEX_FILE_MAGIC_36, 0),
            (constants.DEX_FILE_MAGIC_37, 0),
            (constants.DEX_FILE_MAGIC_38, 0),
            (constants.DEX_FILE_MAGIC_39, 0),
        ),
        "description": "DEX",
    }
    endian = LITTLE_ENDIAN

    def __init__(self, stream, **args):
        LOGGER.info("DEX Parser")
        RootSeekableFieldSet.__init__(
            self, None, "root", stream, None, stream.askSize(self)
        )
        HachoirParser.__init__(self, stream, **args)

    def createFields(self):
        LOGGER.info("Creating fields ...")
        yield HeaderItem(self, "header", "header")

        self.seekByte(self["header/map_off"].value, relative=False)
        yield MapList(self, "map_list", "map_list")

        self.seekByte(self["header/string_ids_off"].value, relative=False)
        for index in range(self["header/string_ids_size"].value):
            yield StringIdItem(self, "string_id_item[]")

        for index in range(self["header/string_ids_size"].value):
            # print(self["string_id_item[" + str(index) + "]"])
            self.seekByte(
                self[
                    "string_id_item[" + str(index) + "]/string_data_off"
                ].value,
                relative=False,
            )
            yield StringDataItem(self, "string_data_item[]")

        self.seekByte(self["header/proto_ids_off"].value, relative=False)
        for index in range(self["header/proto_ids_size"].value):
            yield ProtoIdItem(self, "proto_id_item[]")

        self.seekByte(self["header/type_ids_off"].value, relative=False)
        for index in range(self["header/type_ids_size"].value):
            yield TypeIdItem(self, "type_id_item[]")

        self.seekByte(self["header/method_ids_off"].value, relative=False)
        for index in range(self["header/method_ids_size"].value):
            yield MethodIdItem(self, "method_id_item[]")

        self.seekByte(self["header/class_defs_off"].value, relative=False)
        for index in range(self["header/class_defs_size"].value):
            yield ClassDefItem(self, "class_id_item[]")

        class_data_item = self["map_list"].get_class_data_item()
        if class_data_item:
            self.seekByte(
                class_data_item["offset"].value
                + class_data_item["offset"].value % 4,
                relative=False,
            )
            for index in range(class_data_item["size"].value):
                yield ClassDataItem(self, "class_data_item[]")

        code_item = self["map_list"].get_code_item()
        if code_item:
            self.seekByte(code_item["offset"].value, relative=False)
            for index in range(code_item["size"].value):
                yield CodeItem(self, "code_item[]")

    def validate(self):
        LOGGER.info("validate")
        len_magic = len(constants.DEX_FILE_MAGIC_35)

        if self.stream.readBytes(0, len_magic) not in [
            constants.DEX_FILE_MAGIC_35,
            constants.DEX_FILE_MAGIC_36,
            constants.DEX_FILE_MAGIC_37,
            constants.DEX_FILE_MAGIC_38,
            constants.DEX_FILE_MAGIC_39,
        ]:
            return "Invalid magic"

        err = self["header"].isValid()
        if err:
            return err
        return True


class MethodHelper(object):
    def __init__(self, name, type_method):
        self.name = name
        self.type_method = type_method


class DEXHelper(object):
    def __init__(self, raw_dex: DEX):
        self.raw_dex: DEX = raw_dex
        self.raw_dex.validate()

    @staticmethod
    def from_rawdex(raw_dex: DEX):
        return DEXHelper(raw_dex)

    @staticmethod
    def from_string(data):
        raw = io.BytesIO(data)
        raw.seek(0)
        return DEXHelper.from_rawdex(DEX(StringInputStream(raw.read())))

    def print(self):
        for field in self.raw_dex:
            LOGGER.info(
                "%s:%s %s=%s [%d]"
                % (
                    hex(field.address),
                    hex(field.absolute_address),
                    field.name,
                    field.display,
                    field.size,
                )
            )
        print(self.raw_dex['header'])
        for field in self.raw_dex['header']:
            LOGGER.info(
                "%s:%s %s=%s [%d]"
                % (
                    hex(field.address),
                    hex(field.absolute_address),
                    field.name,
                    field.display,
                    field.size,
                )
            )

        for field in self.raw_dex['map_list']:
            LOGGER.info(
                "%s:%s %s=%s [%d]"
                % (
                    hex(field.address),
                    hex(field.absolute_address),
                    field.name,
                    field.display,
                    field.size,
                )
            )
            if "map_item" in field.name:
                for sub_field in field:
                    LOGGER.info(
                        "\t%s:%s %s=%s [%d]"
                        % (
                            hex(sub_field.address),
                            hex(sub_field.absolute_address),
                            sub_field.name,
                            sub_field.display,
                            sub_field.size,
                        )
                    )

    def get_classes(self) -> Iterator[ClassDefItem]:
        for index in range(self.raw_dex["header/class_defs_size"].value):
            yield self.raw_dex["class_id_item[%d]" % index]

    def get_strings(self) -> Iterator[str]:
        for index in range(self.raw_dex["header/string_ids_size"].value):
            try:
                yield self.raw_dex["string_data_item[%d]/data" % index].value
            except MissingField:
                pass

    def get_string_by_idx(self, idx):
        return self.raw_dex["string_data_item[%d]/data" % idx].value

    def get_method_name(self, idx) -> str:
        try:
            name_idx = self.raw_dex["method_id_item[%d]/name_idx" % idx].value
            return self.get_string_by_idx(name_idx)
        except MissingField:
            return "Unknown @%s" % hex(idx)

    def get_type_value(self, idx) -> str:
        try:
            descriptor_idx = self.raw_dex[
                "type_id_item[%d]/descriptor_idx" % idx
            ].value
            return self.get_string_by_idx(descriptor_idx)
        except MissingField:
            return ""

    def get_methods(self) -> Iterator[MethodHelper]:
        class_data_item = self.raw_dex["map_list"].get_class_data_item()
        for index in range(class_data_item["size"].value):
            prev = 0
            try:
                for index_method in range(
                    self.raw_dex[
                        "class_data_item[%d]/direct_methods_size" % index
                    ].value
                ):
                    method_idx_diff = self.raw_dex[
                        "class_data_item[%d]/direct_methods[%d]/method_idx_diff"
                        % (index, index_method)
                    ].value
                    method_idx = method_idx_diff + prev
                    yield MethodHelper(self.get_method_name(method_idx), 'D')
                    prev = method_idx
            except MissingField:
                LOGGER.warning("MissingField")

            prev = 0
            try:
                for index_method in range(
                    self.raw_dex[
                        "class_data_item[%d]/virtual_methods_size" % index
                    ].value
                ):
                    method_idx_diff = self.raw_dex[
                        "class_data_item[%d]/virtual_methods[%d]/method_idx_diff"
                        % (index, index_method)
                    ].value
                    method_idx = method_idx_diff + prev
                    yield MethodHelper(self.get_method_name(method_idx), 'V')
                    prev = method_idx
            except MissingField:
                LOGGER.warning("MissingField")
