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
    parser.add_argument('-s', '--strings',  action='store_true', help='Extract strings from the DEX')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    args = parser.parse_args()
    return args


arguments = initParser()


def app():
    if arguments.input:
        d = DEX(FileInputStream(arguments.input))
        dh = DEXHelper.from_rawdex(d)

        print(dh)

        for method in dh.get_methods():
            print("START", method)
            code = method.get_code()
            if code:
                print(code["debug_info_off"], code["insns_size"])
            print("END")

    return 0


if __name__ == '__main__':
    app()
