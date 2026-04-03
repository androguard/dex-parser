//! Multi-DEX support: unified view across multiple DEX files.
//!
//! Wraps multiple `DexHelper` instances and provides unified iterators
//! that tag each item with its source DEX file.

use std::fs;
use std::path::Path;

use crate::dex::{
    is_dex, ClassInfo, DexFile, DexHelper, FieldInfoItem, MethodInfoItem,
};
use crate::error::{DexError, Result};

/// Identifies which DEX file an item came from.
#[derive(Clone, Debug)]
pub struct DexSource {
    pub filename: String,
    pub dex_index: usize,
}

/// Wraps any item with its source DEX provenance.
#[derive(Clone, Debug)]
pub struct Sourced<T> {
    pub source: DexSource,
    pub inner: T,
}

/// Unified view across multiple DEX files.
pub struct MultiDexHelper {
    sources: Vec<DexSource>,
    helpers: Vec<DexHelper>,
}

/// Extract the numeric sort key from a DEX filename.
/// `classes.dex` → 0, `classes2.dex` → 2, `classes10.dex` → 10.
fn dex_sort_key(name: &str) -> u32 {
    let stem = name.trim_end_matches(".dex");
    let digits = stem.trim_start_matches("classes");
    if digits.is_empty() {
        0
    } else {
        digits.parse().unwrap_or(u32::MAX)
    }
}

/// Check if a filename matches the `classes*.dex` pattern.
fn is_multidex_name(name: &str) -> bool {
    if !name.ends_with(".dex") {
        return false;
    }
    let stem = name.trim_end_matches(".dex");
    if stem == "classes" {
        return true;
    }
    if let Some(rest) = stem.strip_prefix("classes") {
        rest.chars().all(|c| c.is_ascii_digit()) && !rest.is_empty()
    } else {
        false
    }
}

impl MultiDexHelper {
    /// Create from pre-parsed DEX files with their filenames.
    pub fn new(entries: Vec<(String, DexFile)>) -> Self {
        let mut sources = Vec::with_capacity(entries.len());
        let mut helpers = Vec::with_capacity(entries.len());
        for (idx, (filename, dex)) in entries.into_iter().enumerate() {
            sources.push(DexSource {
                filename,
                dex_index: idx,
            });
            helpers.push(DexHelper::from_dex(&dex));
        }
        Self { sources, helpers }
    }

    /// Scan a directory for `classes*.dex` files, sorted by numeric suffix.
    pub fn from_directory(dir: &Path) -> Result<Self> {
        let mut dex_files: Vec<(String, Vec<u8>)> = Vec::new();

        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().to_string();
            if is_multidex_name(&name) {
                let data = fs::read(entry.path())?;
                if is_dex(&data) {
                    dex_files.push((name, data));
                }
            }
        }

        dex_files.sort_by_key(|(name, _)| dex_sort_key(name));

        if dex_files.is_empty() {
            return Err(DexError::NoDexFiles(dir.display().to_string()));
        }

        let mut entries = Vec::with_capacity(dex_files.len());
        for (name, data) in dex_files {
            let dex = DexFile::parse(&data)?;
            entries.push((name, dex));
        }
        Ok(Self::new(entries))
    }

    /// Extract and parse all DEX files from an APK (ZIP archive).
    #[cfg(feature = "apk")]
    pub fn from_apk(path: &Path) -> Result<Self> {
        use std::io::Read;

        let file = fs::File::open(path)?;
        let mut archive =
            zip::ZipArchive::new(file).map_err(|e| DexError::Parse(format!("ZIP error: {e}")))?;

        let mut dex_names: Vec<String> = (0..archive.len())
            .filter_map(|i| {
                let entry = archive.by_index(i).ok()?;
                let name = entry.name().to_string();
                if is_multidex_name(&name) {
                    Some(name)
                } else {
                    None
                }
            })
            .collect();
        dex_names.sort_by_key(|n| dex_sort_key(n));

        if dex_names.is_empty() {
            return Err(DexError::NoDexFiles(path.display().to_string()));
        }

        let mut entries = Vec::with_capacity(dex_names.len());
        for name in &dex_names {
            let mut entry = archive
                .by_name(name)
                .map_err(|e| DexError::Parse(format!("ZIP entry error: {e}")))?;
            let mut buf = Vec::new();
            entry
                .read_to_end(&mut buf)
                .map_err(|e| DexError::Parse(format!("ZIP read error: {e}")))?;
            let dex = DexFile::parse(&buf)?;
            entries.push((name.clone(), dex));
        }
        Ok(Self::new(entries))
    }

    /// Number of DEX files loaded.
    pub fn dex_count(&self) -> usize {
        self.sources.len()
    }

    /// The source descriptors for all loaded DEX files.
    pub fn dex_sources(&self) -> &[DexSource] {
        &self.sources
    }

    /// Get the DexHelper (and underlying DexFile) for a given DEX index.
    pub fn get_helper(&self, dex_index: usize) -> Option<&DexHelper> {
        self.helpers.get(dex_index)
    }

    /// Get the underlying DexFile for a given DEX index.
    pub fn get_dex(&self, dex_index: usize) -> Option<&DexFile> {
        self.helpers.get(dex_index).map(|h| h.dex())
    }

    /// Iterate over all classes across all DEX files.
    pub fn classes(&self) -> impl Iterator<Item = Result<Sourced<ClassInfo>>> + '_ {
        self.helpers
            .iter()
            .zip(self.sources.iter())
            .flat_map(|(helper, source)| {
                let source = source.clone();
                helper.classes().map(move |result| {
                    result.map(|inner| Sourced {
                        source: source.clone(),
                        inner,
                    })
                })
            })
    }

    /// Iterate over all methods across all DEX files.
    pub fn methods(&self) -> impl Iterator<Item = Result<Sourced<MethodInfoItem>>> + '_ {
        self.helpers
            .iter()
            .zip(self.sources.iter())
            .flat_map(|(helper, source)| {
                let source = source.clone();
                helper.methods().map(move |result| {
                    result.map(|inner| Sourced {
                        source: source.clone(),
                        inner,
                    })
                })
            })
    }

    /// Iterate over all fields across all DEX files.
    pub fn fields(&self) -> impl Iterator<Item = Result<Sourced<FieldInfoItem>>> + '_ {
        self.helpers
            .iter()
            .zip(self.sources.iter())
            .flat_map(|(helper, source)| {
                let source = source.clone();
                helper.fields().map(move |result| {
                    result.map(|inner| Sourced {
                        source: source.clone(),
                        inner,
                    })
                })
            })
    }

    /// Iterate over all strings across all DEX files.
    pub fn strings(&self) -> impl Iterator<Item = Result<Sourced<String>>> + '_ {
        self.helpers
            .iter()
            .zip(self.sources.iter())
            .flat_map(|(helper, source)| {
                let source = source.clone();
                helper.strings().map(move |result| {
                    result.map(|inner| Sourced {
                        source: source.clone(),
                        inner,
                    })
                })
            })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_helpers::minimal_dex_bytes;

    #[test]
    fn test_dex_sort_key() {
        assert_eq!(dex_sort_key("classes.dex"), 0);
        assert_eq!(dex_sort_key("classes2.dex"), 2);
        assert_eq!(dex_sort_key("classes3.dex"), 3);
        assert_eq!(dex_sort_key("classes10.dex"), 10);
        assert!(dex_sort_key("classes.dex") < dex_sort_key("classes2.dex"));
        assert!(dex_sort_key("classes2.dex") < dex_sort_key("classes10.dex"));
    }

    #[test]
    fn test_is_multidex_name() {
        assert!(is_multidex_name("classes.dex"));
        assert!(is_multidex_name("classes2.dex"));
        assert!(is_multidex_name("classes10.dex"));
        assert!(!is_multidex_name("other.dex"));
        assert!(!is_multidex_name("classes.txt"));
        assert!(!is_multidex_name("classes"));
        assert!(!is_multidex_name("classesX.dex"));
    }

    #[test]
    fn test_multi_dex_empty() {
        let multi = MultiDexHelper::new(vec![]);
        assert_eq!(multi.dex_count(), 0);
        assert_eq!(multi.classes().count(), 0);
        assert_eq!(multi.methods().count(), 0);
        assert_eq!(multi.fields().count(), 0);
        assert_eq!(multi.strings().count(), 0);
    }

    #[test]
    fn test_multi_dex_single() {
        let data = minimal_dex_bytes();
        let dex = DexFile::parse(&data).unwrap();
        let multi = MultiDexHelper::new(vec![("classes.dex".to_string(), dex)]);

        assert_eq!(multi.dex_count(), 1);
        assert_eq!(multi.dex_sources()[0].filename, "classes.dex");
        assert_eq!(multi.dex_sources()[0].dex_index, 0);
        assert_eq!(multi.classes().count(), 0);
        assert_eq!(multi.methods().count(), 0);
        assert_eq!(multi.fields().count(), 0);
        assert_eq!(multi.strings().count(), 0);
    }

    #[test]
    fn test_multi_dex_two() {
        let data1 = minimal_dex_bytes();
        let data2 = minimal_dex_bytes();
        let dex1 = DexFile::parse(&data1).unwrap();
        let dex2 = DexFile::parse(&data2).unwrap();
        let multi = MultiDexHelper::new(vec![
            ("classes.dex".to_string(), dex1),
            ("classes2.dex".to_string(), dex2),
        ]);

        assert_eq!(multi.dex_count(), 2);
        assert_eq!(multi.dex_sources()[0].filename, "classes.dex");
        assert_eq!(multi.dex_sources()[0].dex_index, 0);
        assert_eq!(multi.dex_sources()[1].filename, "classes2.dex");
        assert_eq!(multi.dex_sources()[1].dex_index, 1);
    }

    #[test]
    fn test_from_directory() {
        let dir = std::env::temp_dir().join("dex_parser_test_multidex");
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();

        let dex_bytes = minimal_dex_bytes();
        fs::write(dir.join("classes.dex"), &dex_bytes).unwrap();
        fs::write(dir.join("classes2.dex"), &dex_bytes).unwrap();
        fs::write(dir.join("not_a_dex.txt"), b"hello").unwrap();

        let multi = MultiDexHelper::from_directory(&dir).unwrap();
        assert_eq!(multi.dex_count(), 2);
        assert_eq!(multi.dex_sources()[0].filename, "classes.dex");
        assert_eq!(multi.dex_sources()[1].filename, "classes2.dex");

        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_from_directory_empty() {
        let dir = std::env::temp_dir().join("dex_parser_test_empty");
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();

        let result = MultiDexHelper::from_directory(&dir);
        assert!(result.is_err());

        let _ = fs::remove_dir_all(&dir);
    }

    /// Integration test: parse a real multi-DEX APK and verify the unified view.
    /// Requires the `apk` feature and the test fixture at the expected path.
    /// Run with: cargo test --features apk test_real_apk -- --ignored
    #[test]
    #[cfg(feature = "apk")]
    #[ignore] // requires external fixture
    fn test_real_apk_multidex() {
        let apk_path = Path::new("/Users/nkapi/Downloads/ticketmaster/base.apk");
        if !apk_path.exists() {
            eprintln!("Skipping: test fixture not found at {}", apk_path.display());
            return;
        }

        let multi = MultiDexHelper::from_apk(apk_path).unwrap();

        // Ticketmaster has 10 DEX files
        assert_eq!(multi.dex_count(), 10);

        // Verify sort order
        assert_eq!(multi.dex_sources()[0].filename, "classes.dex");
        assert_eq!(multi.dex_sources()[1].filename, "classes2.dex");
        assert_eq!(multi.dex_sources()[9].filename, "classes10.dex");

        // Verify dex_index is sequential
        for (i, src) in multi.dex_sources().iter().enumerate() {
            assert_eq!(src.dex_index, i);
        }

        // Collect classes and verify items come from multiple DEX files
        let classes: Vec<_> = multi.classes().filter_map(|c| c.ok()).collect();
        assert!(classes.len() > 10_000, "expected many classes, got {}", classes.len());

        let mut dex_files_with_classes = std::collections::HashSet::new();
        for c in &classes {
            dex_files_with_classes.insert(c.source.filename.clone());
        }
        assert!(
            dex_files_with_classes.len() >= 5,
            "expected classes from multiple DEX files, got from: {:?}",
            dex_files_with_classes
        );

        // Verify classes from the first DEX have the right source tag
        let first_dex_classes: Vec<_> = classes
            .iter()
            .filter(|c| c.source.filename == "classes.dex")
            .collect();
        assert!(!first_dex_classes.is_empty());

        // Verify classes from the last DEX have the right source tag
        let last_dex_classes: Vec<_> = classes
            .iter()
            .filter(|c| c.source.filename == "classes10.dex")
            .collect();
        assert!(!last_dex_classes.is_empty());

        // Methods should also span multiple DEX files
        let methods: Vec<_> = multi.methods().filter_map(|m| m.ok()).collect();
        assert!(methods.len() > 50_000, "expected many methods, got {}", methods.len());

        let mut dex_files_with_methods = std::collections::HashSet::new();
        for m in &methods {
            dex_files_with_methods.insert(m.source.filename.clone());
        }
        assert!(
            dex_files_with_methods.len() >= 5,
            "expected methods from multiple DEX files, got from: {:?}",
            dex_files_with_methods
        );

        // Fields
        let fields: Vec<_> = multi.fields().filter_map(|f| f.ok()).collect();
        assert!(fields.len() > 10_000, "expected many fields, got {}", fields.len());

        // Strings
        let strings: Vec<_> = multi.strings().filter_map(|s| s.ok()).collect();
        assert!(strings.len() > 10_000, "expected many strings, got {}", strings.len());

        let mut dex_files_with_strings = std::collections::HashSet::new();
        for s in &strings {
            dex_files_with_strings.insert(s.source.filename.clone());
        }
        assert!(
            dex_files_with_strings.len() >= 5,
            "expected strings from multiple DEX files, got from: {:?}",
            dex_files_with_strings
        );
    }
}
