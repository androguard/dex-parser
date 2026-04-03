//! Error types for DEX parsing.

use thiserror::Error;

#[derive(Error, Debug)]
pub enum DexError {
    #[error("DEX parse error: {0}")]
    Parse(String),

    #[error("Invalid magic or unsupported DEX version")]
    InvalidMagic,

    #[error("Truncated or out of bounds: {0}")]
    Truncated(String),

    #[error("No DEX files found in {0}")]
    NoDexFiles(String),

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, DexError>;
