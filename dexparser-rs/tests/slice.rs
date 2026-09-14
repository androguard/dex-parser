//! DexSlicer tests — plan §13.5, §13.6, §13.9.

use dex_parser::{fix_checksums, DexBuilder, DexError, DexFile, DexSlicer};
use std::path::PathBuf;

fn fixture() -> Vec<u8> {
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../dex-decompiler/testdata/androguard_test_classes.dex");
    std::fs::read(&p).unwrap_or_else(|_| panic!("missing {}", p.display()))
}

#[test]
fn slice_roundtrip_structural() {
    let data = fixture();
    let src = DexFile::parse(&data).unwrap();
    let targets: Vec<String> = src
        .class_defs()
        .filter_map(|r| r.ok())
        .filter_map(|cd| src.get_type(cd.class_idx).ok())
        .take(12)
        .collect();
    assert!(!targets.is_empty());
    for desc in targets {
        let slicer = DexSlicer::new(&data).unwrap();
        let sliced = match slicer.slice_class(&desc) {
            Ok(b) => b,
            Err(DexError::UnsupportedRef) => continue,
            Err(e) => panic!("slice {desc}: {e}"),
        };
        let out = DexFile::parse(&sliced).unwrap_or_else(|e| panic!("parse slice {desc}: {e}"));
        assert_eq!(out.header.class_defs_size, 1);
        let cd = out.get_class_def(0).unwrap();
        assert_eq!(out.get_type(cd.class_idx).unwrap(), desc);
        let src_cd = src
            .class_defs()
            .filter_map(|r| r.ok())
            .find(|c| src.get_type(c.class_idx).ok().as_deref() == Some(desc.as_str()))
            .unwrap();
        let src_data = src.get_class_data(&src_cd).unwrap();
        let out_data = out.get_class_data(&cd).unwrap();
        match (src_data, out_data) {
            (None, None) => {}
            (Some(a), Some(b)) => {
                assert_eq!(a.static_fields.len(), b.static_fields.len(), "{desc} static fields");
                assert_eq!(
                    a.instance_fields.len(),
                    b.instance_fields.len(),
                    "{desc} instance fields"
                );
                assert_eq!(
                    a.direct_methods.len(),
                    b.direct_methods.len(),
                    "{desc} direct methods"
                );
                assert_eq!(
                    a.virtual_methods.len(),
                    b.virtual_methods.len(),
                    "{desc} virtual methods"
                );
                for (sm, om) in a
                    .direct_methods
                    .iter()
                    .chain(a.virtual_methods.iter())
                    .zip(b.direct_methods.iter().chain(b.virtual_methods.iter()))
                {
                    let si = src.get_method_info(sm.method_idx).unwrap();
                    let oi = out.get_method_info(om.method_idx).unwrap();
                    assert_eq!(si.name, oi.name, "{desc} method name");
                    assert_eq!(si.return_type, oi.return_type);
                    assert_eq!(si.params, oi.params);
                    if sm.code_off != 0 && om.code_off != 0 {
                        let sc = src.get_code_item(sm.code_off).unwrap();
                        let oc = out.get_code_item(om.code_off).unwrap();
                        assert_eq!(sc.insns_size, oc.insns_size, "{desc}#{} insns", si.name);
                        assert_eq!(sc.registers_size, oc.registers_size);
                    }
                }
            }
            other => panic!("{desc} class_data mismatch: {other:?}"),
        }
    }
}

#[test]
fn slice_validity_checksum_stable() {
    let data = fixture();
    let src = DexFile::parse(&data).unwrap();
    let desc = src
        .class_defs()
        .filter_map(|r| r.ok())
        .find_map(|cd| src.get_type(cd.class_idx).ok())
        .unwrap();
    let slicer = DexSlicer::new(&data).unwrap();
    let mut sliced = slicer.slice_class(&desc).unwrap();
    assert_eq!(sliced.len() as u32, DexFile::parse(&sliced).unwrap().header.file_size);
    let mut again = sliced.clone();
    fix_checksums(&mut again).unwrap();
    assert_eq!(sliced, again);
    // string_ids sorted by content
    let dex = DexFile::parse(&sliced).unwrap();
    let mut prev = String::new();
    for i in 0..dex.header.string_ids_size {
        let s = dex.get_string(i).unwrap();
        assert!(s >= prev, "string_ids not sorted at {i}");
        prev = s;
    }
}

#[test]
fn slice_preflight_unsupported_ref() {
    // Build a tiny class then patch an invoke-custom (0xfc) into the code.
    let mut b = DexBuilder::new();
    b.intern_type("Ljava/lang/Object;");
    use dex_parser::{BuiltClass, BuiltCode, BuiltMethod};
    let class = BuiltClass {
        descriptor: "Lcom/test/Custom;".into(),
        access_flags: 1,
        superclass: Some("Ljava/lang/Object;".into()),
        interfaces: vec![],
        source_file: None,
        static_fields: vec![],
        instance_fields: vec![],
        direct_methods: vec![BuiltMethod {
            class: "Lcom/test/Custom;".into(),
            name: "foo".into(),
            proto: "()V".into(),
            access_flags: 1,
            code: Some(BuiltCode {
                registers_size: 1,
                ins_size: 0,
                outs_size: 0,
                // nop; return-void — will patch first insn to invoke-custom
                insns: vec![0x00, 0x00, 0x0e, 0x00],
                tries: vec![],
                debug_info_off: 0,
                debug_ops: vec![],
            }),
            direct: true,
        }],
        virtual_methods: vec![],
        annotations: Default::default(),
    };
    b.add_class(class);
    let mut bytes = b.finish().unwrap();
    fix_checksums(&mut bytes).unwrap();
    // Find code and patch opcode to 0xfc (still 6-byte form needs padding — use 0xfe const-method-handle = 2 bytes)
    // Locate "nop" (00 00) and set to fe 00 (const-method-handle) — preflight rejects 0xfe.
    let mut patched = bytes.clone();
    let mut found = false;
    for i in 0..patched.len().saturating_sub(1) {
        if patched[i] == 0x00 && patched[i + 1] == 0x00 {
            // skip header nops; look for sequence followed by return-void
            if i + 3 < patched.len() && patched[i + 2] == 0x0e && patched[i + 3] == 0x00 {
                patched[i] = 0xfe;
                found = true;
                break;
            }
        }
    }
    assert!(found, "could not locate nop;return-void to patch");
    fix_checksums(&mut patched).unwrap();
    let err = DexSlicer::new(&patched)
        .unwrap()
        .slice_class("Lcom/test/Custom;")
        .unwrap_err();
    assert!(
        matches!(err, DexError::UnsupportedRef),
        "expected UnsupportedRef, got {err}"
    );
}
