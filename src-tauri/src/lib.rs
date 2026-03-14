pub mod generator;
pub mod patterns;
pub mod export;

use std::path::PathBuf;

#[tauri::command]
fn generate_pattern(config: generator::PatternConfig) -> Result<Vec<generator::CutPath>, String> {
    let paths = config.generate();
    Ok(paths)
}

#[tauri::command]
fn generate_pattern_parallel(config: generator::PatternConfig) -> Result<Vec<generator::CutPath>, String> {
    // With the new model, generate_cut already returns multiple paths.
    // Just delegate to the standard generate path.
    let paths = config.generate();
    Ok(paths)
}

#[tauri::command]
fn generate_extended_pattern(
    surface: generator::SurfaceType,
    pattern: patterns::PatternType,
    cut_count: usize,
    cut_angle_offset: f64,
) -> Result<Vec<generator::CutPath>, String> {
    let base_cut = pattern.generate_path(0.0);

    let mut paths: Vec<generator::CutPath> = Vec::new();
    for i in 0..cut_count {
        let angle = i as f64 * cut_angle_offset;
        let mut cut = base_cut.clone();
        cut.rotate(angle);

        // Apply boundary clipping
        for point in &mut cut.points {
            if !surface.is_within_bounds(point.x, point.y)
                || !surface.is_outside_bore(point.x, point.y)
            {
                point.z = 2.0;
            }
        }

        paths.push(cut);
    }

    Ok(paths)
}

/// Primary generation command — multi-zone, eccentric, with bore support.
/// Returns Vec<Vec<CutPath>> indexed by zone.
#[tauri::command]
fn generate_zoned_pattern(
    config: generator::ZonedPatternConfig,
) -> Result<Vec<Vec<generator::CutPath>>, String> {
    if config.zones.is_empty() {
        return Err("At least one zone is required".to_string());
    }
    Ok(config.generate())
}

#[tauri::command]
fn export_pattern_svg(
    paths: Vec<generator::CutPath>,
    file_path: String,
    width: f64,
    height: f64,
) -> Result<(), String> {
    let path = PathBuf::from(file_path);
    export::svg_export::export_svg(&paths, &path, width, height, 0.5)
}

#[tauri::command]
fn export_pattern_config(
    config: generator::ZonedPatternConfig,
    file_path: String,
) -> Result<(), String> {
    let path = PathBuf::from(file_path);
    export::json_export::export_config_json(&config, &path)
}

#[tauri::command]
fn export_pattern_data(
    paths: Vec<generator::CutPath>,
    file_path: String,
) -> Result<(), String> {
    let path = PathBuf::from(file_path);
    export::json_export::export_paths_json(&paths, &path)
}

#[tauri::command]
fn validate_parameters(config: generator::ZonedPatternConfig) -> Result<(), String> {
    if config.zones.is_empty() {
        return Err("At least one zone is required".to_string());
    }

    match &config.surface {
        generator::SurfaceType::Circular(c) => {
            if c.outer_radius <= 0.0 {
                return Err("Circular surface radius must be positive".to_string());
            }
            if c.thickness <= 0.0 {
                return Err("Surface thickness must be positive".to_string());
            }
            if c.inner_radius < 0.0 {
                return Err("Bore radius cannot be negative".to_string());
            }
            if c.inner_radius >= c.outer_radius {
                return Err("Bore radius must be smaller than outer radius".to_string());
            }
        }
        generator::SurfaceType::Rectangular(r) => {
            if r.width <= 0.0 || r.height <= 0.0 {
                return Err("Rectangular surface dimensions must be positive".to_string());
            }
            if r.thickness <= 0.0 {
                return Err("Surface thickness must be positive".to_string());
            }
        }
    }

    for (i, zone) in config.zones.iter().enumerate() {
        if zone.engine.rosette_lobes == 0 {
            return Err(format!("Zone {}: rosette_lobes must be >= 1", i + 1));
        }
        if zone.engine.amplitude < 0.0 {
            return Err(format!("Zone {}: amplitude must be >= 0", i + 1));
        }
        if zone.engine.num_passes == 0 {
            return Err(format!("Zone {}: num_passes must be >= 1", i + 1));
        }
        if zone.engine.radial_step <= 0.0 {
            return Err(format!("Zone {}: radial_step must be positive", i + 1));
        }
        if zone.engine.rotations_per_pass <= 0.0 {
            return Err(format!("Zone {}: rotations_per_pass must be positive", i + 1));
        }
    }

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            generate_pattern,
            generate_pattern_parallel,
            generate_extended_pattern,
            generate_zoned_pattern,
            export_pattern_svg,
            export_pattern_config,
            export_pattern_data,
            validate_parameters
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
