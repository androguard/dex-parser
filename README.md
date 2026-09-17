<p align="center"><img width="120" src="./.github/logo.png"></p>
<h2 align="center">DEX-Parser: The Scalpel for Dalvik Executables</h2>

<div align="center">

![Powered By: Androguard](https://img.shields.io/badge/androguard-green?style=for-the-badge&label=Powered%20by&link=https%3A%2F%2Fgithub.com%2Fandroguard)
![Sponsor](https://img.shields.io/badge/sponsor-nlnet-blue?style=for-the-badge&link=https%3A%2F%2Fnlnet.nl%2F)
![PYPY](https://img.shields.io/badge/PYPI-DEXPARSER-violet?style=for-the-badge&link=https%3A%2F%2Fpypi.org%2Fproject%2Fdexparser-ag%2F)


</div>

# Description

The soul of every Android app is its code, compiled into a compact, efficient Dalvik Executable (DEX) format. `dex-parser` is the surgical tool designed to lay this soul bare.

It is a core pillar of the new Androguard Ecosystem: a **Rust** DEX parser (`dexparser-rs`) with **Python** bindings (`dexparser-py` via PyO3). Use it from pure Rust projects or from Python with the same high-level API (`DEX`, `DEXHelper`).

# Philosophy

Following the "Deconstruct to Reconstruct" philosophy, dex-parser operates as a specialized, independent library. It does not concern itself with the meaning of the bytecode; its singular focus is on perfectly and performantly reading the blueprint of the executable. This separation of concerns makes it a robust and reliable foundation for any tool that needs to understand the structure of Dalvik code.

# Key Features

- **Full structure parsing:** header, string table, type identifiers, method prototypes, field/method ids, class definitions, class data, and code items.
- **Class & method enumeration:** iterate classes, direct/virtual methods, and static/instance fields.
- **Rust core + Python bindings:** fast parsing in Rust; PyO3 module for Python.
- **Magic detection:** recognize DEX by content (`dex\n`), not only by `.dex` extension.
- **CLI tools:** `dexparser` (single file), `dexparse-dir` (batch parse + timing; optional disasm via [dex-bytecode](https://github.com/androguard/dex-bytecode)).
- **[TODO] Multi-DEX aware:** unified view over `classes.dex`, `classes2.dex`, …

## Layout

```
  dex-parser/
  ├── dexparser-rs/     # Rust library (DexFile, DexHelper)
  ├── dexparser-py/     # PyO3 bindings → Python module dexparser_rs
  ├── dexparser/        # Thin Python package (DEX, DEXHelper, CLI)
  └── tests/            # Python binding tests
```

```
  &[u8] / path / stream
         │
         ▼
    DexFile::parse() / DEX(...) / DEX.from_path(...)
         │
         ▼
    DexHelper / DEXHelper
         │
         ├── classes() / get_classes()
         ├── methods() / get_methods()   (+ code_item / get_code())
         └── fields()  / get_fields()
```

---

## Installation

### Python (bindings)

Requires a Rust toolchain. Use a virtual environment:

```bash
git clone https://github.com/androguard/dex-parser.git
cd dex-parser
python3 -m venv .venv && source .venv/bin/activate
pip install maturin
# Python 3.14+: may need PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
maturin develop --manifest-path dexparser-py/Cargo.toml
```

Or via PyPI (when published):

```bash
pip install dexparser-ag
```

### Rust (library)

Add a path (or crates.io) dependency in your `Cargo.toml`:

```toml
[dependencies]
dex-parser = { path = "path/to/dex-parser/dexparser-rs" }
# or when published: dex-parser = "0.1"
```

---

## CLI examples

```bash
# Single file (Python entry point after maturin develop)
dexparser -i classes.dex
dexparser -i classes.dex -s -v

# Rust: parse one file
cargo run --release --manifest-path dexparser-rs/Cargo.toml --bin dexparser -- -i classes.dex

# Rust: parse all DEX in a directory (detect by magic by default)
cargo run --release --manifest-path dexparser-rs/Cargo.toml --bin dexparse-dir -- -d /path/to/dir
cargo run --release --manifest-path dexparser-rs/Cargo.toml --bin dexparse-dir --features disasm -- -d /path/to/dir
```

---

## Python example

```python
from dexparser import DEX, DEXHelper, DEX_from_source, is_dex

# Path, bytes, or stream
d = DEX("classes.dex")
# or: d = DEX.from_path("classes.dex")
# or: d = DEX(open("classes.dex", "rb").read())
# or: d = DEX_from_source(open("classes.dex", "rb"))

print(d)
print(d["header"])  # dict: file_size, class_defs_size, string_ids_size, ...

if is_dex(open("classes.dex", "rb").read()):
    print("valid DEX magic")

dh = DEXHelper.from_rawdex(d)
# or: dh = DEXHelper.from_string(bytes_data)

for cls in dh.get_classes():
    print("CLASS", cls.name, "extends", cls.sname)

for method in dh.get_methods():
    print("METHOD", method.class_name, method.name, method.proto, method.type_method)
    code = method.get_code()
    if code:
        insns = code["insns"].value  # raw Dalvik bytecode (bytes)
        print("  CODE debug_info_off=", code.debug_info_off,
              "insns_size=", code.insns_size, "bytes=", len(insns))

for field in dh.get_fields():
    print("FIELD", field.class_name, field.name, field.type_field)

for s in dh.get_strings():
    print("STRING", s)
```

### ASC fast path (findrefs / getclass primitives)

```python
from dexparser import FastRef, dex_defines_class, slice_class

data = open("classes.dex", "rb").read()

# Does this DEX define Lcom/example/Main; ?
assert dex_defines_class(data, "Lcom/example/Main;")

# Minimal DEX containing only that class
minimal = slice_class(data, "Lcom/example/Main;")

# Raw code_item reference search
fr = FastRef(data)
for site in fr.find_strings("token"):
    print(site.method_idx, site.pool_idx, hex(site.file_off))
for site in fr.find_methods(class_name="Lcom/example/Main;", method_name="onCreate"):
    print(site)
for site in fr.find_method_idx(42):
    print(site)
```

Run binding tests (needs `../dex-decompiler/testdata/classes3.dex` or adjust the path):

```bash
source .venv/bin/activate
pip install pytest
pytest tests/test_bindings.py -v
```

---

## Rust example

```rust
use dex_parser::{DexFile, DexHelper, is_dex};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let bytes = std::fs::read("classes.dex")?;
    if !is_dex(&bytes) {
        eprintln!("not a DEX file");
        return Ok(());
    }

    let dex = DexFile::parse(&bytes)?;
    println!(
        "file_size={} classes={} methods={} strings={}",
        dex.header.file_size,
        dex.header.class_defs_size,
        dex.header.method_ids_size,
        dex.header.string_ids_size,
    );

    let helper = DexHelper::from_dex(&dex);

    for class in helper.classes() {
        let c = class?;
        println!("CLASS {} extends {}", c.name, c.superclass_name);
    }

    for method in helper.methods() {
        let m = method?;
        println!(
            "METHOD {} {} -> {} ({:?})",
            m.info.class, m.info.name, m.info.return_type, m.method_type
        );
        if let Some(code) = &m.code_item {
            let insns = code.insns_slice(&bytes);
            println!(
                "  CODE debug_info_off={} insns_size={} bytes={}",
                code.debug_info_off,
                code.insns_size,
                insns.len()
            );
        }
    }

    for field in helper.fields() {
        let f = field?;
        println!("FIELD {} {} {} ({:?})", f.info.class, f.info.name, f.info.typ, f.field_kind);
    }

    // Low-level
    let class_def = dex.get_class_def(0)?;
    let _class_data = dex.get_class_data(&class_def)?;
    let _string = dex.get_string(0)?;
    let _typ = dex.get_type(0)?;

    Ok(())
}
```

More detail (diagrams, `dexparse-dir`, disasm feature): see [`dexparser-rs/README.md`](dexparser-rs/README.md).

---

## License

Distributed under the [Apache License, Version 2.0](LICENSE).
