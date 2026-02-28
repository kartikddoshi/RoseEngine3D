use crate::generator::Point3D;

/// Generate rose curve (Rhodonea curve)
/// Formula: r = cos(k*θ)
/// Cartesian: x = r*cos(θ), y = r*sin(θ)
pub fn generate_rose_curve(k: f64, amplitude: f64, steps: usize) -> Vec<Point3D> {
    (0..=steps)
        .map(|i| {
            let theta = (i as f64 / 5.0).to_radians();
            let r = (k * theta).cos() * amplitude;
            let x = r * theta.cos();
            let y = r * theta.sin();

            Point3D { x, y, z: 0.0 }
        })
        .collect()
}
