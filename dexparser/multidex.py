"""Multi-DEX support: unified view across multiple DEX files.

Wraps multiple DEXHelper instances and provides unified iterators
that tag each item with its source DEX file.
"""

import os
import re
import zipfile
from dataclasses import dataclass
from typing import Iterator

from . import ClassHelper, DEXHelper, MethodHelper


DEX_PATTERN = re.compile(r'^classes\d*\.dex$')


def _dex_sort_key(name: str) -> int:
    """Extract numeric sort key: classes.dex→0, classes2.dex→2, classes10.dex→10."""
    stem = name.removesuffix('.dex')
    digits = stem.removeprefix('classes')
    if not digits:
        return 0
    try:
        return int(digits)
    except ValueError:
        return 2**31


@dataclass
class DexSource:
    """Identifies which DEX file an item came from."""
    filename: str
    dex_index: int


class MultiDEXHelper:
    """Unified view across multiple DEX files."""

    def __init__(self, helpers: list[tuple[str, DEXHelper]]):
        self._helpers = helpers

    @staticmethod
    def from_apk(apk_path: str) -> 'MultiDEXHelper':
        """Extract and parse all DEX files from an APK (ZIP archive)."""
        helpers = []
        with zipfile.ZipFile(apk_path, 'r') as zf:
            dex_names = sorted(
                [n for n in zf.namelist() if DEX_PATTERN.match(os.path.basename(n))],
                key=_dex_sort_key,
            )
            if not dex_names:
                raise ValueError(f"No DEX files found in {apk_path}")
            for name in dex_names:
                data = zf.read(name)
                helper = DEXHelper.from_string(data)
                helpers.append((os.path.basename(name), helper))
        return MultiDEXHelper(helpers)

    @staticmethod
    def from_directory(dir_path: str) -> 'MultiDEXHelper':
        """Scan a directory for classes*.dex files, sorted by numeric suffix."""
        helpers = []
        dex_files = []
        for name in os.listdir(dir_path):
            if DEX_PATTERN.match(name):
                dex_files.append(name)
        dex_files.sort(key=_dex_sort_key)

        if not dex_files:
            raise ValueError(f"No DEX files found in {dir_path}")

        for name in dex_files:
            path = os.path.join(dir_path, name)
            with open(path, 'rb') as f:
                data = f.read()
            helper = DEXHelper.from_string(data)
            helpers.append((name, helper))
        return MultiDEXHelper(helpers)

    @staticmethod
    def from_dex_files(paths: list[str]) -> 'MultiDEXHelper':
        """Parse multiple DEX files by path."""
        helpers = []
        for path in paths:
            name = os.path.basename(path)
            with open(path, 'rb') as f:
                data = f.read()
            helper = DEXHelper.from_string(data)
            helpers.append((name, helper))
        return MultiDEXHelper(helpers)

    def dex_count(self) -> int:
        return len(self._helpers)

    def dex_sources(self) -> list[DexSource]:
        return [
            DexSource(filename=name, dex_index=idx)
            for idx, (name, _) in enumerate(self._helpers)
        ]

    def get_classes(self) -> Iterator[tuple[DexSource, ClassHelper]]:
        """Iterate over all classes across all DEX files."""
        for idx, (name, helper) in enumerate(self._helpers):
            source = DexSource(filename=name, dex_index=idx)
            for cls in helper.get_classes():
                yield (source, cls)

    def get_methods(self) -> Iterator[tuple[DexSource, MethodHelper]]:
        """Iterate over all methods across all DEX files."""
        for idx, (name, helper) in enumerate(self._helpers):
            source = DexSource(filename=name, dex_index=idx)
            for method in helper.get_methods():
                yield (source, method)

    def get_fields(self):
        """Iterate over all fields across all DEX files."""
        for idx, (name, helper) in enumerate(self._helpers):
            source = DexSource(filename=name, dex_index=idx)
            for field in helper.get_fields():
                yield (source, field)

    def get_strings(self) -> Iterator[tuple[DexSource, str]]:
        """Iterate over all strings across all DEX files."""
        for idx, (name, helper) in enumerate(self._helpers):
            source = DexSource(filename=name, dex_index=idx)
            for s in helper.get_strings():
                yield (source, s)
