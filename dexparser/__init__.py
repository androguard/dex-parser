import io
from dataclasses import dataclass
from typing import Iterator

from hachoir.core.endian import LITTLE_ENDIAN
from hachoir.field import MissingField, RootSeekableFieldSet
from hachoir.parser import HachoirParser
from hachoir.stream import StringInputStream

from dexparser.helper.logging import LOGGER
from dexparser.parser import constants
from dexparser.parser.class_data_item import ClassDataItem
from dexparser.parser.class_def_item import ClassDefItem
from dexparser.parser.code_item import CodeItem
from dexparser.parser.field_id_item import FieldIdItem
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
            self.seekByte(
                self[
                    "string_id_item[" + str(index) + "]/string_data_off"
                ].value,
                relative=False,
            )
            yield StringDataItem(self, "string_data_item[]")

        self.seekByte(self["header/proto_ids_off"].value, relative=False)
        for _ in range(self["header/proto_ids_size"].value):
            yield ProtoIdItem(self, "proto_id_item[]")

        self.seekByte(self["header/type_ids_off"].value, relative=False)
        for _ in range(self["header/type_ids_size"].value):
            yield TypeIdItem(self, "type_id_item[]")

        self.seekByte(self["header/method_ids_off"].value, relative=False)
        for _ in range(self["header/method_ids_size"].value):
            yield MethodIdItem(self, "method_id_item[]")

        self.seekByte(self["header/field_ids_off"].value, relative=False)
        for _ in range(self["header/field_ids_size"].value):
            yield FieldIdItem(self, "field_id_item[]")

        self.seekByte(self["header/class_defs_off"].value, relative=False)
        for _ in range(self["header/class_defs_size"].value):
            yield ClassDefItem(self, "class_id_item[]")

        class_data_item = self["map_list"].get_class_data_item()
        if class_data_item:
            self.seekByte(
                class_data_item["offset"].value,
                relative=False,
            )
            for _ in range(class_data_item["size"].value):
                yield ClassDataItem(self, "class_data_item[]")

            for index in range(class_data_item["size"].value):
                try:
                    for index_method in range(
                        self[
                            "class_data_item[%d]/direct_methods_size" % index
                        ].value
                    ):
                        code_off = self[
                            "class_data_item[%d]/direct_methods[%d]/code_off"
                            % (index, index_method)
                        ].value
                        if code_off > 0:
                            self.seekByte(code_off, relative=False)
                            yield CodeItem(
                                self,
                                "direct_methods_code_%d_%d"
                                % (index, index_method),
                            )

                except MissingField as e:
                    LOGGER.warning("MissingField", str(e))

                try:
                    for index_method in range(
                        self[
                            "class_data_item[%d]/virtual_methods_size" % index
                        ].value
                    ):
                        code_off = self[
                            "class_data_item[%d]/virtual_methods[%d]/code_off"
                            % (index, index_method)
                        ].value
                        if code_off > 0:
                            self.seekByte(code_off, relative=False)
                            yield CodeItem(
                                self,
                                "virtual_methods_code_%d_%d"
                                % (index, index_method),
                            )
                except MissingField as e:
                    LOGGER.warning("MissingField", str(e))

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


@dataclass
class ClassHelper:
    raw_dex: DEX
    name: str
    sname: str


@dataclass
class MethodHelper:
    raw_dex: DEX
    name: str
    class_name: str
    proto: list[str]
    type_method: str
    method_idx: int
    code_off: int
    idx_class: int
    idx: int

    def get_internal_struct(self):
        if self.type_method == 'V':
            return self.raw_dex[
                f"class_data_item[{self.idx_class}]/virtual_methods[{self.idx}]"
            ]

        return self.raw_dex[
            f"class_data_item[{self.idx_class}]/direct_methods[{self.idx}]"
        ]

    def get_code(self):
        if self.code_off <= 0:
            return None

        if self.type_method == 'V':
            return self.raw_dex[
                "virtual_methods_code_%d_%d" % (self.idx_class, self.idx)
            ]
        return self.raw_dex[
            "direct_methods_code_%d_%d" % (self.idx_class, self.idx)
        ]


@dataclass
class FieldHelper:
    raw_dex: DEX
    name: str
    class_name: str
    type_field: str
    idx_class: int
    idx: int

    def get_internal_struct(self):
        if self.type_field == 'S':
            return self.raw_dex[
                f"class_data_item[{self.idx_class}]/static_fields[{self.idx}]"
            ]

        return self.raw_dex[
            f"class_data_item[{self.idx_class}]/instance_fields[{self.idx}]"
        ]


class DEXHelper(object):
    def __init__(self, raw_dex: DEX):
        self.raw_dex: DEX = raw_dex
        self.raw_dex.validate()

        self.__cached_strings = {}

    @staticmethod
    def from_rawdex(raw_dex: DEX):
        return DEXHelper(raw_dex)

    @staticmethod
    def from_string(data):
        raw = io.BytesIO(data)
        raw.seek(0)
        return DEXHelper.from_rawdex(DEX(StringInputStream(raw.read())))

    def get_classes(self) -> Iterator[ClassDefItem]:
        for index in range(self.raw_dex["header/class_defs_size"].value):
            yield ClassHelper(
                self.raw_dex,
                self._get_class_name(index),
                self._get_sclass_name(index),
            )

    def get_strings(self) -> Iterator[str]:
        for index in range(self.raw_dex["header/string_ids_size"].value):
            try:
                yield self.raw_dex["string_data_item[%d]/data" % index].value
            except MissingField:
                pass

    def get_string_by_idx(self, idx):
        if idx in self.__cached_strings:
            return self.__cached_strings[idx]

        data = self.raw_dex["string_data_item[%d]/data" % idx].value
        self.__cached_strings[idx] = data
        return data

    def _get_sclass_name(self, idx):
        superclass_idx = self.raw_dex[
            "class_id_item[%d]/superclass_idx" % idx
        ].value
        name_idx = self.raw_dex[
            "type_id_item[%d]/descriptor_idx" % superclass_idx
        ].value
        return self.get_string_by_idx(name_idx)

    def _get_class_name(self, idx):
        class_idx = self.raw_dex["class_id_item[%d]/class_idx" % idx].value
        name_idx = self.raw_dex[
            "type_id_item[%d]/descriptor_idx" % class_idx
        ].value
        return self.get_string_by_idx(name_idx)

    def _get_proto(self, idx) -> list[str]:
        try:
            proto_idx = self.raw_dex[
                "method_id_item[%d]/proto_idx" % idx
            ].value
            shorty_idx = self.raw_dex[
                "proto_id_item[%d]/shorty_idx" % proto_idx
            ].value

            return_type_idx = self.raw_dex[
                "proto_id_item[%d]/return_type_idx" % proto_idx
            ].value
            descriptor_idx = self.raw_dex[
                "type_id_item[%d]/descriptor_idx" % return_type_idx
            ].value

            return [
                self.get_string_by_idx(shorty_idx),
                self.get_string_by_idx(descriptor_idx),
            ]
        except MissingField:
            return []

    def _get_method_class_name(self, idx) -> str:
        try:
            class_idx = self.raw_dex[
                "method_id_item[%d]/class_idx" % idx
            ].value
            name_idx = self.raw_dex[
                "type_id_item[%d]/descriptor_idx" % class_idx
            ].value
            return self.get_string_by_idx(name_idx)
        except MissingField:
            return "Unknown @%s" % hex(idx)

    def _get_method_name(self, idx) -> str:
        try:
            name_idx = self.raw_dex["method_id_item[%d]/name_idx" % idx].value
            return self.get_string_by_idx(name_idx)
        except MissingField:
            return "Unknown @%s" % hex(idx)

    def _get_field_class_name(self, idx) -> str:
        try:
            class_idx = self.raw_dex["field_id_item[%d]/class_idx" % idx].value
            name_idx = self.raw_dex[
                "type_id_item[%d]/descriptor_idx" % class_idx
            ].value
            return self.get_string_by_idx(name_idx)
        except MissingField:
            return "Unknown @%s" % hex(idx)

    def _get_field_name(self, idx) -> str:
        try:
            name_idx = self.raw_dex["field_id_item[%d]/name_idx" % idx].value
            return self.get_string_by_idx(name_idx)
        except MissingField:
            return "Unknown @%s" % hex(idx)

    def _get_type_value(self, idx) -> str:
        try:
            descriptor_idx = self.raw_dex[
                "type_id_item[%d]/descriptor_idx" % idx
            ].value
            return self.get_string_by_idx(descriptor_idx)
        except MissingField:
            return ""

    def get_methods(self) -> Iterator[MethodHelper]:
        class_data_item = self.raw_dex["map_list"].get_class_data_item()
        if not class_data_item:
            return

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
                    code_off = self.raw_dex[
                        "class_data_item[%d]/direct_methods[%d]/code_off"
                        % (index, index_method)
                    ].value
                    method_idx = method_idx_diff + prev
                    yield MethodHelper(
                        self.raw_dex,
                        self._get_method_name(method_idx),
                        self._get_method_class_name(method_idx),
                        self._get_proto(method_idx),
                        'D',
                        method_idx,
                        code_off,
                        index,
                        index_method,
                    )
                    prev = method_idx
            except MissingField:
                LOGGER.warning("Direct Method MissingField")

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
                    code_off = self.raw_dex[
                        "class_data_item[%d]/virtual_methods[%d]/code_off"
                        % (index, index_method)
                    ].value
                    method_idx = method_idx_diff + prev
                    yield MethodHelper(
                        self.raw_dex,
                        self._get_method_name(method_idx),
                        self._get_method_class_name(method_idx),
                        self._get_proto(method_idx),
                        'V',
                        method_idx,
                        code_off,
                        index,
                        index_method,
                    )
                    prev = method_idx
            except MissingField:
                LOGGER.warning("Virtual Method MissingField")

    def get_fields(self) -> Iterator[MethodHelper]:
        class_data_item = self.raw_dex["map_list"].get_class_data_item()
        if not class_data_item:
            return

        for index in range(class_data_item["size"].value):
            prev = 0
            try:
                for index_field in range(
                    self.raw_dex[
                        "class_data_item[%d]/static_fields_size" % index
                    ].value
                ):
                    field_idx_diff = self.raw_dex[
                        "class_data_item[%d]/static_fields[%d]/field_idx_diff"
                        % (index, index_field)
                    ].value
                    field_idx = field_idx_diff + prev
                    yield FieldHelper(
                        self.raw_dex,
                        self._get_field_name(field_idx),
                        self._get_field_class_name(field_idx),
                        'S',
                        index,
                        index_field,
                    )
                    prev = field_idx
            except MissingField:
                LOGGER.warning("Static Field MissingField")

            prev = 0
            try:
                for index_field in range(
                    self.raw_dex[
                        "class_data_item[%d]/instance_fields_size" % index
                    ].value
                ):
                    field_idx_diff = self.raw_dex[
                        "class_data_item[%d]/instance_fields[%d]/field_idx_diff"
                        % (index, index_field)
                    ].value
                    field_idx = field_idx_diff + prev
                    yield FieldHelper(
                        self.raw_dex,
                        self._get_field_name(field_idx),
                        self._get_field_class_name(field_idx),
                        'I',
                        index,
                        index_field,
                    )
                    prev = field_idx
            except MissingField:
                LOGGER.warning("Instance Field MissingField")
