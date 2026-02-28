use crate::generator::Point3D;

/// Generate epitrochoid or hypotrochoid points
pub fn generate_trochoid(
    fixed_radius: f64,
    rolling_radius: f64,
    cam_amplitude: f64,
    phase_shift: f64,
    is_epitrochoid: bool,
    steps: usize,
) -> Vec<Point3D> {
    let phase = phase_shift.to_radians();

    (0..=steps)
        .map(|i| {
            let theta = (i as f64 / 5.0).to_radians();
            let t = theta + phase;

            let (x, y) = if is_epitrochoid {
                // Epitrochoid: rolling outside
                let sum = fixed_radius + rolling_radius;
                let x = sum * t.cos() - cam_amplitude * ((sum / rolling_radius) * t).cos();
                let y = sum * t.sin() - cam_amplitude * ((sum / rolling_radius) * t).sin();
                (x, y)
            } else {
                // Hypotrochoid: rolling inside
                let diff = fixed_radius - rolling_radius;
                let x = diff * t.cos() + cam_amplitude * ((diff / rolling_radius) * t).cos();
                let y = diff * t.sin() - cam_amplitude * ((diff / rolling_radius) * t).sin();
                (x, y)
            };

            Point3D { x, y, z: 0.0 }
        })
        .collect()
}
