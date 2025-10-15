<p align="center"><img width="120" src="./.github/logo.png"></p>
<h2 align="center">DEX-Parser: The Scalpel for Dalvik Executables</h2>

<div align="center">

![Powered By: Androguard](https://img.shields.io/badge/androguard-green?style=for-the-badge&label=Powered%20by&link=https%3A%2F%2Fgithub.com%2Fandroguard)

</div>

# Description

The soul of every Android app is its code, compiled into a compact, efficient Dalvik Executable (DEX) format. `dex-parser` is the surgical tool designed to lay this soul bare.

This is a standalone, dependency-free, native Python library built to parse the complete structure of DEX files. It is a core pillar of the new Androguard Ecosystem, providing a high-fidelity map of an application's code layout—its classes, methods, fields, and strings—before deeper analysis begins.

# Philosophy

Following the "Deconstruct to Reconstruct" philosophy, dex-parser operates as a specialized, independent library. It does not concern itself with the meaning of the bytecode; its singular focus is on perfectly and performantly reading the blueprint of the executable. This separation of concerns makes it a robust and reliable foundation for any tool that needs to understand the structure of Dalvik code.

# Key Features


- Full Structure Parsing: Reads and indexes the entire DEX file, including the header, string table, type identifiers, method prototypes, and class definitions.
- Class & Method Enumeration: Provides a clean, Pythonic API to iterate through all defined classes, their methods (both direct and virtual), and their fields.
- On demand access for each fields by using [Hachoir library](https://github.com/vstinner/hachoir).
- Cross-Reference Ready: Lays the groundwork for building cross-references by cleanly separating method and field definitions from their invocations.
- Pure & Pythonic: Written in native Python with zero external dependencies for maximum portability.
- [TODO] Multi-DEX Aware: Natively understands and can parse classes.dex, classes2.dex, and so on, providing a unified view of the application's code.

## Installation

If you would like to install it locally, please create a new venv to use it directly, and then:

```
$ git clone https://github.com/androguard/dex-parser.git
$ pip install -e .
```

or directly via pypi:
```
$ pip install dexparser-ag
```

## Examples

You can directly use it by command line to parse and display quickly information about a DEX file, but the purpose of this tool is mainly to be a library for other tools like Androguard.

```
$ dexparser -i Test.dex
```

## Usage

You can open a dex file directly by using the ```DEX``` class:
```
from hachoir.stream.input_helper import FileInputStream
from dexparser import DEX

d = DEX(FileInputStream(arguments.input))
```

and use directly the raw access to each field of the DEX structure, like the header, 
and after access to each subfields:
```
print(d["header"])
print(d["headermagic/magic"].value)
```

Or you can use the ```DEXHelper``` class to quickly get access to class name, method name,
field name, but also code item for each method for disassembling:

```
from dexparser import DEXHelper
dh = DEXHelper.from_rawdex(d)

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
            my_func_to_disassemble(code["insns"].value)
```
## License

Distributed under the [Apache License, Version 2.0](LICENSE).

