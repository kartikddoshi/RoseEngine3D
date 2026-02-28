use crate::generator::Point3D;
use super::SpiralType;

/// Generate spiral curve
/// Archimedean: r = a + b*θ
/// Logarithmic: r = a*e^(b*θ)
pub fn generate_spiral(
    spiral_type: &SpiralType,
    a: f64,
    b: f64,
    steps: usize,
) -> Vec<Point3D> {
    (0..=steps)
        .map(|i| {
            let theta = (i as f64 / 5.0).to_radians();

            let r = match spiral_type {
                SpiralType::Archimedean => a + b * theta,
                SpiralType::Logarithmic => a * (b * theta).exp(),
            };

            let x = r * theta.cos();
            let y = r * theta.sin();

            Point3D { x, y, z: 0.0 }
        })
        .collect()
}
