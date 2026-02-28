use crate::generator::Point3D;

/// Generate Lissajous curve
/// x = A*sin(a*t + δ)
/// y = B*sin(b*t)
pub fn generate_lissajous(
    freq_x: f64,
    freq_y: f64,
    phase: f64,
    amp_x: f64,
    amp_y: f64,
    steps: usize,
) -> Vec<Point3D> {
    let phase_rad = phase.to_radians();

    (0..=steps)
        .map(|i| {
            let t = (i as f64 / 5.0).to_radians();
            let x = amp_x * (freq_x * t + phase_rad).sin();
            let y = amp_y * (freq_y * t).sin();

            Point3D { x, y, z: 0.0 }
        })
        .collect()
}
