import argparse

from hachoir.stream.input_helper import FileInputStream

from . import DEX, DEXHelper
from .helper.logging import LOGGER


def initParser():
    parser = argparse.ArgumentParser(
        prog='dexparser',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='DEX Parser',
    )

    parser.add_argument('-i', '--input', type=str, help='Input DEX file')
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
    if arguments.input:
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

    return 0


if __name__ == '__main__':
    app()
