use serde::{Deserialize, Serialize};
use crate::generator::{Point3D, CutPath};

pub mod trochoid;
pub mod rose;
pub mod lissajous;
pub mod spiral;
pub mod compositor;

/// Pattern generation trait - all pattern types implement this
pub trait Pattern: Send + Sync {
    fn generate(&self, steps: usize) -> Vec<Point3D>;
    fn name(&self) -> &str;
}

/// Unified pattern type enum
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "pattern_type")]
pub enum PatternType {
    Trochoid {
        fixed_radius: f64,
        rolling_radius: f64,
        cam_amplitude: f64,
        phase_shift: f64,
        is_epitrochoid: bool,
        rotations: f64,
    },
    RoseCurve {
        k: f64,           // Petal count (frequency)
        amplitude: f64,   // Overall size
        rotations: f64,   // How many full circles to draw
    },
    Lissajous {
        freq_x: f64,      // X frequency
        freq_y: f64,      // Y frequency
        phase: f64,       // Phase shift in degrees
        amp_x: f64,       // X amplitude
        amp_y: f64,       // Y amplitude
        rotations: f64,   // Duration
    },
    Spiral {
        spiral_type: SpiralType,
        a: f64,           // Starting radius
        b: f64,           // Growth factor
        rotations: f64,   // Number of rotations
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SpiralType {
    Archimedean,
    Logarithmic,
}

impl PatternType {
    /// Generate a cut path from this pattern type
    pub fn generate_path(&self, surface_thickness: f64) -> CutPath {
        let steps = match self {
            PatternType::Trochoid { rotations, .. } => (rotations * 360.0 * 5.0) as usize,
            PatternType::RoseCurve { rotations, .. } => (rotations * 360.0 * 5.0) as usize,
            PatternType::Lissajous { rotations, .. } => (rotations * 360.0 * 5.0) as usize,
            PatternType::Spiral { rotations, .. } => (rotations * 360.0 * 5.0) as usize,
        };

        let mut points = match self {
            PatternType::Trochoid {
                fixed_radius,
                rolling_radius,
                cam_amplitude,
                phase_shift,
                is_epitrochoid,
                rotations: _
            } => {
                trochoid::generate_trochoid(
                    *fixed_radius,
                    *rolling_radius,
                    *cam_amplitude,
                    *phase_shift,
                    *is_epitrochoid,
                    steps,
                )
            },
            PatternType::RoseCurve { k, amplitude, rotations: _ } => {
                rose::generate_rose_curve(*k, *amplitude, steps)
            },
            PatternType::Lissajous { freq_x, freq_y, phase, amp_x, amp_y, rotations: _ } => {
                lissajous::generate_lissajous(*freq_x, *freq_y, *phase, *amp_x, *amp_y, steps)
            },
            PatternType::Spiral { spiral_type, a, b, rotations: _ } => {
                spiral::generate_spiral(spiral_type, *a, *b, steps)
            },
        };

        // Set Z coordinate to surface thickness
        for point in &mut points {
            point.z = surface_thickness;
        }

        CutPath { points }
    }
}
