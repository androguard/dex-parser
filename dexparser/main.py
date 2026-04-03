import argparse

from hachoir.stream.input_helper import FileInputStream

from . import DEX, DEXHelper
from .multidex import MultiDEXHelper
from .helper.logging import LOGGER


def initParser():
    parser = argparse.ArgumentParser(
        prog='dexparser',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='DEX Parser',
    )

    parser.add_argument('-i', '--input', type=str, help='Input DEX file')
    parser.add_argument('--apk', type=str, help='Input APK file (extracts all DEX files)')
    parser.add_argument('--dir', type=str, help='Directory containing DEX files')
    parser.add_argument(
        '-s',
        '--strings',
        action='store_true',
        help='Extract strings from the DEX',
    )
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    args = parser.parse_args()
    return args


arguments = initParser()


def app():
    if arguments.apk or arguments.dir:
        _run_multi()
    elif arguments.input:
        _run_single()
    else:
        print("Error: provide --input, --apk, or --dir")
        return 1
    return 0


def _run_single():
    d = DEX(FileInputStream(arguments.input))
    dh = DEXHelper.from_rawdex(d)

    print(dh)
    print(d["header"])

    for _class in dh.get_classes():
        print("CLASS", _class)

    for method in dh.get_methods():
        print("METHOD", method, method.get_internal_struct())
        code = method.get_code()
        if code:
            print(
                "\t CODE",
                code["debug_info_off"],
                code["insns_size"],
                len(code["insns"].value),
            )

    for field in dh.get_fields():
        print("FIELD", field, field.get_internal_struct())


def _run_multi():
    if arguments.apk:
        multi = MultiDEXHelper.from_apk(arguments.apk)
    else:
        multi = MultiDEXHelper.from_directory(arguments.dir)

    print(f"Loaded {multi.dex_count()} DEX file(s)")
    for src in multi.dex_sources():
        print(f"  [{src.filename}] (index {src.dex_index})")
    print()

    for source, _class in multi.get_classes():
        print(f"[{source.filename}] CLASS", _class)

    for source, method in multi.get_methods():
        print(f"[{source.filename}] METHOD", method)

    for source, field in multi.get_fields():
        print(f"[{source.filename}] FIELD", field)

    if arguments.strings:
        for source, s in multi.get_strings():
            print(f"[{source.filename}] STRING", s)


if __name__ == '__main__':
    app()
