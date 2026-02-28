use crate::generator::{Point3D, CutPath};

#[derive(Debug, Clone)]
pub enum BlendMode {
    Add,
    Multiply,
    Subtract,
}

/// Combine two cut paths using a blend mode
pub fn blend_paths(path1: &CutPath, path2: &CutPath, mode: BlendMode, opacity: f64) -> CutPath {
    // For simplicity, we'll work with paths of equal length
    // In production, we'd interpolate/resample to match lengths
    let min_len = path1.points.len().min(path2.points.len());

    let points = (0..min_len)
        .map(|i| {
            let p1 = &path1.points[i];
            let p2 = &path2.points[i];

            match mode {
                BlendMode::Add => Point3D {
                    x: p1.x + p2.x * opacity,
                    y: p1.y + p2.y * opacity,
                    z: p1.z,
                },
                BlendMode::Multiply => Point3D {
                    x: p1.x * (1.0 + p2.x * opacity / 100.0),
                    y: p1.y * (1.0 + p2.y * opacity / 100.0),
                    z: p1.z,
                },
                BlendMode::Subtract => Point3D {
                    x: p1.x - p2.x * opacity,
                    y: p1.y - p2.y * opacity,
                    z: p1.z,
                },
            }
        })
        .collect();

    CutPath { points }
}
