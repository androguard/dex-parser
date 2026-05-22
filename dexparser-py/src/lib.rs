//! Python bindings for dex-parser (Rust DEX parser).

use dex_parser::{DexFile, DexHelper, FieldKind, MethodType};
use pyo3::exceptions::{PyIOError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyType};
use std::fs;

fn dex_err(e: dex_parser::DexError) -> PyErr {
    PyValueError::new_err(e.to_string())
}

fn header_to_dict<'py>(py: Python<'py>, h: &dex_parser::DexHeader) -> PyResult<Bound<'py, PyDict>> {
    let d = PyDict::new(py);
    d.set_item("file_size", h.file_size)?;
    d.set_item("header_size", h.header_size)?;
    d.set_item("endian_tag", h.endian_tag)?;
    d.set_item("map_off", h.map_off)?;
    d.set_item("string_ids_size", h.string_ids_size)?;
    d.set_item("string_ids_off", h.string_ids_off)?;
    d.set_item("type_ids_size", h.type_ids_size)?;
    d.set_item("type_ids_off", h.type_ids_off)?;
    d.set_item("proto_ids_size", h.proto_ids_size)?;
    d.set_item("proto_ids_off", h.proto_ids_off)?;
    d.set_item("field_ids_size", h.field_ids_size)?;
    d.set_item("field_ids_off", h.field_ids_off)?;
    d.set_item("method_ids_size", h.method_ids_size)?;
    d.set_item("method_ids_off", h.method_ids_off)?;
    d.set_item("class_defs_size", h.class_defs_size)?;
    d.set_item("class_defs_off", h.class_defs_off)?;
    d.set_item("data_size", h.data_size)?;
    d.set_item("data_off", h.data_off)?;
    Ok(d)
}

/// Parsed DEX file (Rust backend).
#[pyclass(name = "DEX", unsendable)]
struct PyDexFile {
    dex: DexFile,
    data: Vec<u8>,
}

#[pymethods]
impl PyDexFile {
    #[new]
    fn new(data: Vec<u8>) -> PyResult<Self> {
        let dex = DexFile::parse(&data).map_err(dex_err)?;
        Ok(Self { dex, data })
    }

    #[classmethod]
    fn from_path(_cls: &Bound<'_, PyType>, path: String) -> PyResult<Self> {
        let data = fs::read(&path).map_err(|e| PyIOError::new_err(e.to_string()))?;
        Self::new(data)
    }

    #[classmethod]
    fn from_bytes(_cls: &Bound<'_, PyType>, data: Vec<u8>) -> PyResult<Self> {
        Self::new(data)
    }

    fn validate(&self) -> PyResult<()> {
        if !dex_parser::is_dex(&self.data) {
            return Err(PyValueError::new_err("Invalid magic"));
        }
        Ok(())
    }

    fn header<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        header_to_dict(py, &self.dex.header)
    }

    fn __getitem__<'py>(&self, py: Python<'py>, key: &str) -> PyResult<PyObject> {
        match key {
            "header" => Ok(self.header(py)?.into_any().unbind()),
            _ => Err(PyValueError::new_err(format!("unknown field: {key}"))),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "DEX(file_size={}, class_defs_size={})",
            self.dex.header.file_size, self.dex.header.class_defs_size
        )
    }
}

/// Code item with instruction bytes.
#[pyclass]
#[derive(Clone)]
struct PyCodeItem {
    #[pyo3(get)]
    debug_info_off: u32,
    #[pyo3(get)]
    insns_size: u32,
    insns: Vec<u8>,
}

#[pymethods]
impl PyCodeItem {
    fn __getitem__<'py>(&self, py: Python<'py>, key: &str) -> PyResult<PyObject> {
        match key {
            "debug_info_off" => Ok(self.debug_info_off.into_pyobject(py)?.into_any().unbind()),
            "insns_size" => Ok(self.insns_size.into_pyobject(py)?.into_any().unbind()),
            "insns" => Ok(PyInsnsField {
                value: self.insns.clone(),
            }
            .into_pyobject(py)?
            .into_any()
            .unbind()),
            _ => Err(PyValueError::new_err(format!("unknown field: {key}"))),
        }
    }
}

#[pyclass]
struct PyInsnsField {
    value: Vec<u8>,
}

#[pymethods]
impl PyInsnsField {
    #[getter]
    fn value(&self) -> Vec<u8> {
        self.value.clone()
    }
}

#[pyclass(name = "ClassHelper")]
struct PyClassHelper {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    sname: String,
}

#[pymethods]
impl PyClassHelper {
    fn __repr__(&self) -> String {
        format!("ClassHelper(name={:?}, sname={:?})", self.name, self.sname)
    }
}

#[pyclass(name = "MethodHelper")]
struct PyMethodHelper {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    class_name: String,
    #[pyo3(get)]
    proto: Vec<String>,
    #[pyo3(get)]
    type_method: String,
    #[pyo3(get)]
    method_idx: u32,
    #[pyo3(get)]
    code_off: u32,
    #[pyo3(get)]
    idx_class: u32,
    #[pyo3(get)]
    idx: u32,
    code_item: Option<PyCodeItem>,
}

#[pymethods]
impl PyMethodHelper {
    fn get_code(&self) -> Option<PyCodeItem> {
        self.code_item.clone()
    }

    fn get_internal_struct<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let d = PyDict::new(py);
        d.set_item("method_idx", self.method_idx)?;
        d.set_item("code_off", self.code_off)?;
        d.set_item("type_method", &self.type_method)?;
        Ok(d)
    }

    fn __repr__(&self) -> String {
        format!(
            "MethodHelper({} {} {:?})",
            self.class_name, self.name, self.type_method
        )
    }
}

#[pyclass(name = "FieldHelper")]
struct PyFieldHelper {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    class_name: String,
    #[pyo3(get)]
    type_field: String,
    #[pyo3(get)]
    idx_class: u32,
    #[pyo3(get)]
    idx: u32,
}

#[pymethods]
impl PyFieldHelper {
    fn get_internal_struct<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let d = PyDict::new(py);
        d.set_item("type_field", &self.type_field)?;
        d.set_item("idx_class", self.idx_class)?;
        d.set_item("idx", self.idx)?;
        Ok(d)
    }

    fn __repr__(&self) -> String {
        format!("FieldHelper({} {})", self.class_name, self.name)
    }
}

#[pyclass(name = "DEXHelper", unsendable)]
struct PyDexHelper {
    helper: DexHelper,
    data: Vec<u8>,
    string_cache: std::collections::HashMap<u32, String>,
}

#[pymethods]
impl PyDexHelper {
    #[staticmethod]
    fn from_rawdex(dex: &PyDexFile) -> PyResult<Self> {
        dex.validate()?;
        let helper = DexHelper::from_dex(&dex.dex);
        Ok(Self {
            helper,
            data: dex.data.clone(),
            string_cache: std::collections::HashMap::new(),
        })
    }

    #[staticmethod]
    fn from_string(data: Vec<u8>) -> PyResult<Self> {
        let dex = PyDexFile::new(data)?;
        Self::from_rawdex(&dex)
    }

    fn get_classes<'py>(&self, py: Python<'py>) -> PyResult<Vec<Bound<'py, PyClassHelper>>> {
        let mut out = Vec::new();
        for c in self.helper.classes() {
            let c = c.map_err(dex_err)?;
            out.push(PyClassHelper {
                name: c.name,
                sname: c.superclass_name,
            }
            .into_pyobject(py)?);
        }
        Ok(out)
    }

    fn get_strings(&self) -> PyResult<Vec<String>> {
        self.helper
            .strings()
            .map(|r| r.map_err(dex_err))
            .collect()
    }

    fn get_string_by_idx(&mut self, idx: u32) -> PyResult<String> {
        if let Some(s) = self.string_cache.get(&idx) {
            return Ok(s.clone());
        }
        let s = self.helper.dex().get_string(idx).map_err(dex_err)?;
        self.string_cache.insert(idx, s.clone());
        Ok(s)
    }

    fn get_methods<'py>(&self, py: Python<'py>) -> PyResult<Vec<Bound<'py, PyMethodHelper>>> {
        let mut out = Vec::new();
        let mut class_idx = 0u32;
        let mut method_idx_in_class = 0u32;
        let mut last_class = String::new();

        for m in self.helper.methods() {
            let m = m.map_err(dex_err)?;
            if m.info.class != last_class {
                if !last_class.is_empty() {
                    class_idx += 1;
                }
                method_idx_in_class = 0;
                last_class = m.info.class.clone();
            }

            let type_method = match m.method_type {
                MethodType::Direct => "D",
                MethodType::Virtual => "V",
            };
            let mut proto = vec![m.info.return_type.clone()];
            proto.extend(m.info.params.clone());

            let code_item = m.code_item.as_ref().map(|code| PyCodeItem {
                debug_info_off: code.debug_info_off,
                insns_size: code.insns_size,
                insns: code.insns_slice(&self.data).to_vec(),
            });

            out.push(
                PyMethodHelper {
                    name: m.info.name,
                    class_name: m.info.class,
                    proto,
                    type_method: type_method.to_string(),
                    method_idx: m.method_idx,
                    code_off: m.code_off,
                    idx_class: class_idx,
                    idx: method_idx_in_class,
                    code_item,
                }
                .into_pyobject(py)?,
            );
            method_idx_in_class += 1;
        }
        Ok(out)
    }

    fn get_fields<'py>(&self, py: Python<'py>) -> PyResult<Vec<Bound<'py, PyFieldHelper>>> {
        let mut out = Vec::new();
        let mut class_idx = 0u32;
        let mut field_idx_in_class = 0u32;
        let mut last_class = String::new();

        for f in self.helper.fields() {
            let f = f.map_err(dex_err)?;
            if f.info.class != last_class {
                if !last_class.is_empty() {
                    class_idx += 1;
                }
                field_idx_in_class = 0;
                last_class = f.info.class.clone();
            }
            let type_field = match f.field_kind {
                FieldKind::Static => "S",
                FieldKind::Instance => "I",
            };
            out.push(
                PyFieldHelper {
                    name: f.info.name,
                    class_name: f.info.class,
                    type_field: type_field.to_string(),
                    idx_class: class_idx,
                    idx: field_idx_in_class,
                }
                .into_pyobject(py)?,
            );
            field_idx_in_class += 1;
        }
        Ok(out)
    }

    fn __repr__(&self) -> String {
        "DEXHelper(...)".to_string()
    }
}

/// Check if bytes look like a DEX file (magic `dex\\n`).
#[pyfunction]
fn is_dex(data: &[u8]) -> bool {
    dex_parser::is_dex(data)
}

#[pymodule]
fn dexparser_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyDexFile>()?;
    m.add_class::<PyDexHelper>()?;
    m.add_class::<PyClassHelper>()?;
    m.add_class::<PyMethodHelper>()?;
    m.add_class::<PyFieldHelper>()?;
    m.add_class::<PyCodeItem>()?;
    m.add_function(wrap_pyfunction!(is_dex, m)?)?;
    Ok(())
}
