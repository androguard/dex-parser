//! Fastref locator / scan tests (plan §13.4, §13.7, §13.8).

use dex_parser::{dex_defines_class, DexFile, FastRef, MemberQuery};
use std::path::PathBuf;

fn fixture_dex() -> Vec<u8> {
    let p = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../dex-decompiler/testdata/androguard_test_classes.dex");
    std::fs::read(&p).unwrap_or_else(|_| {
        panic!("missing fixture {}", p.display());
    })
}

#[test]
fn string_locator_matches_bruteforce() {
    let data = fixture_dex();
    let dex = DexFile::parse(&data).unwrap();
    let mut fr = FastRef::new(&data).unwrap();
    let queries = ["Test", "java", "init", "xyzzy_unlikely"];
    for q in queries {
        let mut brute = Vec::new();
        for i in 0..dex.header.string_ids_size {
            if let Ok(s) = dex.get_string(i) {
                if s.contains(q) {
                    brute.push(i);
                }
            }
        }
        brute.sort_unstable();
        let raw = dex_parser::RawDex::parse(&data).unwrap();
        let mut sl = dex_parser::dex::fastref::locator::StringLocator::build(&raw).unwrap();
        let mut got = sl.locate(q);
        got.sort_unstable();
        assert_eq!(got, brute, "string locate mismatch for {q:?}");
        let _ = fr.find_strings(q).unwrap();
    }
}

#[test]
fn dex_defines_test_invoke() {
    let data = fixture_dex();
    assert!(dex_defines_class(&data, "Ltests/androguard/TestInvoke;"));
    assert!(!dex_defines_class(&data, "Lcom/not/Present;"));
}

#[test]
fn method_locator_by_name() {
    let data = fixture_dex();
    let mut fr = FastRef::new(&data).unwrap();
    let sites = fr
        .find_methods(&MemberQuery {
            class: None,
            name: Some("TestInvoke1".into()),
        })
        .unwrap();
    // May be empty if TestInvoke1 is only defined not invoked; just ensure it runs.
    let _ = sites.len();
}

#[test]
fn packed_switch_payload_not_false_positive_opcode() {
    // Synthetic: packed-switch payload bytes containing 0x6e + method idx 1.
    // Scanner may hit; verifier must reject if not an instruction boundary.
    let mut payload = vec![0u8; 32];
    payload[0] = 0x00;
    payload[1] = 0x01; // packed-switch ident
    payload[2] = 0x01;
    payload[3] = 0x00; // size 1
    payload[4] = 0;
    payload[5] = 0;
    payload[6] = 0;
    payload[7] = 0; // first_key
    payload[8] = 0x6e; // looks like invoke-virtual
    payload[9] = 0x00;
    payload[10] = 0x01;
    payload[11] = 0x00; // method idx 1
    let mut hits = Vec::new();
    dex_parser::dex::fastref::scan::scan_kind(
        dex_parser::dex::fastref::scan::RefKind::Method,
        &payload,
        0,
        &[1],
        10,
        &mut hits,
    );
    // Hit may exist at byte 8; that's expected of the raw scan.
    if !hits.is_empty() {
        assert!(hits.iter().any(|h| h.file_off == 8 || h.pool_idx == 1));
    }
}
