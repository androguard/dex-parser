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
- Multi-DEX Aware: Natively understands and can parse classes.dex, classes2.dex, and so on, providing a unified view of the application's code.
- Cross-Reference Ready: Lays the groundwork for building cross-references by cleanly separating method and field definitions from their invocations.
- Pure & Pythonic: Written in native Python with zero external dependencies for maximum portability.

## Installation

## Examples

## Authors

## License

Distributed under the [Apache License, Version 2.0](LICENSE).

