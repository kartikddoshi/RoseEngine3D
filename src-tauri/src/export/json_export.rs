use crate::generator::{ZonedPatternConfig, CutPath};
use std::fs::File;
use std::io::Write;
use std::path::Path;
use serde_json;

/// Export zoned pattern configuration as JSON
pub fn export_config_json(config: &ZonedPatternConfig, file_path: &Path) -> Result<(), String> {
    let json = serde_json::to_string_pretty(config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    let mut file = File::create(file_path)
        .map_err(|e| format!("Failed to create JSON file: {}", e))?;

    file.write_all(json.as_bytes())
        .map_err(|e| format!("Failed to write JSON: {}", e))?;

    Ok(())
}

/// Export generated paths as JSON
pub fn export_paths_json(paths: &[CutPath], file_path: &Path) -> Result<(), String> {
    let json = serde_json::to_string_pretty(paths)
        .map_err(|e| format!("Failed to serialize paths: {}", e))?;

    let mut file = File::create(file_path)
        .map_err(|e| format!("Failed to create JSON file: {}", e))?;

    file.write_all(json.as_bytes())
        .map_err(|e| format!("Failed to write JSON: {}", e))?;

    Ok(())
}
