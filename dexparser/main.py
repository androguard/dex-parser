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
            print(method)


        #if arguments.strings:
        #    print([i for i in dh.get_strings()])


    return 0


if __name__ == '__main__':
    app()
