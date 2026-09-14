//! Zero-copy DEX header / table views over `&[u8]`.

use crate::error::{DexError, Result};
use crate::leb128::read_u32;

use super::DexFile;

/// Table view: `(offset, size)` of id items.
#[derive(Debug, Clone, Copy)]
pub struct TableView {
    pub off: u32,
    pub size: u32,
}

/// Header offsets for fastref without constructing a full [`DexFile`].
#[derive(Debug, Clone)]
pub struct RawDex<'a> {
    pub data: &'a [u8],
    pub string_ids: TableView,
    pub type_ids: TableView,
    pub proto_ids: TableView,
    pub field_ids: TableView,
    pub method_ids: TableView,
    pub class_defs: TableView,
    pub map_off: u32,
}

impl<'a> RawDex<'a> {
    pub fn parse(data: &'a [u8]) -> Result<Self> {
        if data.len() < 0x70 || &data[0..4] != b"dex\n" {
            return Err(DexError::InvalidMagic);
        }
        let map_off = read_u32(data, 0x34).ok_or(DexError::Truncated("map_off".into()))?;
        let string_ids = table(data, 0x38, 0x3c)?;
        let type_ids = table(data, 0x40, 0x44)?;
        let proto_ids = table(data, 0x48, 0x4c)?;
        let field_ids = table(data, 0x50, 0x54)?;
        let method_ids = table(data, 0x58, 0x5c)?;
        let class_defs = table(data, 0x60, 0x64)?;
        Ok(Self {
            data,
            string_ids,
            type_ids,
            proto_ids,
            field_ids,
            method_ids,
            class_defs,
            map_off,
        })
    }

    pub fn from_dex(dex: &'a DexFile) -> Self {
        Self {
            data: &*dex.data,
            string_ids: TableView {
                off: dex.header.string_ids_off,
                size: dex.header.string_ids_size,
            },
            type_ids: TableView {
                off: dex.header.type_ids_off,
                size: dex.header.type_ids_size,
            },
            proto_ids: TableView {
                off: dex.header.proto_ids_off,
                size: dex.header.proto_ids_size,
            },
            field_ids: TableView {
                off: dex.header.field_ids_off,
                size: dex.header.field_ids_size,
            },
            method_ids: TableView {
                off: dex.header.method_ids_off,
                size: dex.header.method_ids_size,
            },
            class_defs: TableView {
                off: dex.header.class_defs_off,
                size: dex.header.class_defs_size,
            },
            map_off: dex.header.map_off,
        }
    }

    #[inline]
    pub fn u32_at(&self, off: usize) -> Result<u32> {
        read_u32(self.data, off).ok_or_else(|| DexError::Truncated(format!("u32@{off}")))
    }

    #[inline]
    pub fn u16_at(&self, off: usize) -> Result<u16> {
        if off + 2 > self.data.len() {
            return Err(DexError::Truncated(format!("u16@{off}")));
        }
        Ok(u16::from_le_bytes([self.data[off], self.data[off + 1]]))
    }

    /// Absolute offset of `string_ids[i]`'s `string_data_item`.
    pub fn string_data_off(&self, idx: u32) -> Result<u32> {
        if idx >= self.string_ids.size {
            return Err(DexError::Truncated("string index".into()));
        }
        self.u32_at(self.string_ids.off as usize + idx as usize * 4)
    }

    /// Descriptor string_idx for `type_ids[i]`.
    pub fn type_descriptor_idx(&self, idx: u32) -> Result<u32> {
        if idx >= self.type_ids.size {
            return Err(DexError::Truncated("type index".into()));
        }
        self.u32_at(self.type_ids.off as usize + idx as usize * 4)
    }

    /// Read MUTF-8 payload bytes (excluding uleb128 size and trailing NUL) for a string_id.
    pub fn string_payload_bytes(&self, idx: u32) -> Result<&'a [u8]> {
        let offset = self.string_data_off(idx)? as usize;
        let (_utf16, n) = crate::leb128::read_uleb128(self.data, offset)
            .ok_or(DexError::Truncated("utf16_size".into()))?;
        let start = offset + n;
        let mut end = start;
        while end < self.data.len() && self.data[end] != 0 {
            end += 1;
        }
        Ok(&self.data[start..end])
    }

    /// Look up map_list entry of `type_` (e.g. `0x2001` CODE_ITEM). Returns `(size, offset)`.
    pub fn map_entry(&self, type_: u16) -> Option<(u32, u32)> {
        if self.map_off == 0 {
            return None;
        }
        let off = self.map_off as usize;
        if off + 4 > self.data.len() {
            return None;
        }
        let size = u32::from_le_bytes(self.data[off..off + 4].try_into().ok()?) as usize;
        let mut p = off + 4;
        for _ in 0..size {
            if p + 12 > self.data.len() {
                return None;
            }
            let t = u16::from_le_bytes([self.data[p], self.data[p + 1]]);
            let count = u32::from_le_bytes(self.data[p + 4..p + 8].try_into().ok()?);
            let offset = u32::from_le_bytes(self.data[p + 8..p + 12].try_into().ok()?);
            if t == type_ {
                return Some((count, offset));
            }
            p += 12;
        }
        None
    }
}

fn table(data: &[u8], size_off: usize, off_off: usize) -> Result<TableView> {
    Ok(TableView {
        size: read_u32(data, size_off).ok_or(DexError::Truncated("table size".into()))?,
        off: read_u32(data, off_off).ok_or(DexError::Truncated("table off".into()))?,
    })
}
