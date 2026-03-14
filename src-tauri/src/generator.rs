use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum SurfaceType {
    Circular(CircularSurface),
    Rectangular(RectangularSurface),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CircularSurface {
    /// Outer radius of the workpiece in mm
    pub outer_radius: f64,
    /// Bore (inner hole) radius in mm. 0.0 = solid disk.
    pub inner_radius: f64,
    /// Plate thickness in mm
    pub thickness: f64,
    /// Workpiece center offset from spindle axis in mm (X)
    pub eccentricity_x: f64,
    /// Workpiece center offset from spindle axis in mm (Y)
    pub eccentricity_y: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RectangularSurface {
    pub width: f64,
    pub height: f64,
    pub thickness: f64,
}

/// A single coordinate in the generated pattern
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Point3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// A continuous path cut by the virtual tool
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CutPath {
    pub points: Vec<Point3D>,
}

impl CutPath {
    /// Rotate the entire cut path around the Z-axis (spindle center) by a given angle in degrees.
    pub fn rotate(&mut self, angle_degrees: f64) {
        let angle_rad = angle_degrees.to_radians();
        let cos_a = angle_rad.cos();
        let sin_a = angle_rad.sin();
        for p in &mut self.points {
            let new_x = p.x * cos_a - p.y * sin_a;
            let new_y = p.x * sin_a + p.y * cos_a;
            p.x = new_x;
            p.y = new_y;
        }
    }
}

/// How the phase changes between successive concentric passes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CrossingType {
    /// Concentric waves — no phase change between passes
    None,
    /// Barleycorn/Grain d'Orge — phase advances linearly per pass
    Linear,
    /// Basketweave — phase zigzags: up for N passes, then down for N passes
    Basketweave,
    /// Moiré — two interleaved sets with slightly offset lobe counts
    Moire,
}

/// Rose Engine parameters — the primary engine model.
/// Each parameter set generates many concentric sinusoidal passes,
/// exactly as a real rose engine does.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoseEngineParams {
    /// Number of lobes on the rosette cam (e.g. 6, 8, 12, 24, 72)
    pub rosette_lobes: u32,
    /// Amplitude of the rosette cam oscillation in mm
    pub amplitude: f64,
    /// Number of concentric passes from outer to inner radius
    pub num_passes: u32,
    /// Radial spacing between passes in mm
    pub radial_step: f64,
    /// Crossing type: how phase changes between passes
    /// Serialised as a plain string: "none" | "linear" | "basketweave" | "moire"
    pub crossing_type: String,
    /// Phase increment per pass in degrees (used by Linear and Basketweave)
    pub phase_increment: f64,
    /// Number of cuts before phase reversal in Basketweave mode
    pub basketweave_count: u32,
    /// Total spindle rotations per pass (usually 1.0)
    pub rotations_per_pass: f64,
}

/// Legacy single-pattern config (kept for backward compat with export commands)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PatternConfig {
    pub surface: SurfaceType,
    pub engine: RoseEngineParams,
    pub cut_count: usize,
    pub cut_angle_offset: f64,
}

impl PatternConfig {
    pub fn generate(&self) -> Vec<CutPath> {
        let zone_bounds = None;
        self.surface.generate_cut(&self.engine, zone_bounds)
    }
}

/// An annular zone on the workpiece with its own pattern parameters.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PatternZone {
    /// Inner radius of this zone from spindle axis in mm
    pub inner_radius: f64,
    /// Outer radius of this zone from spindle axis in mm
    pub outer_radius: f64,
    pub engine: RoseEngineParams,
    /// Kept for backward compat — no longer drives pass count (num_passes does)
    pub cut_count: usize,
    /// Kept for backward compat — unused in primary path
    pub cut_angle_offset: f64,
    /// Hex color string for 3-D visualisation
    pub color: String,
    /// Display label
    pub label: String,
}

/// Multi-zone pattern config — the primary config type for the app.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZonedPatternConfig {
    pub surface: SurfaceType,
    pub zones: Vec<PatternZone>,
}

impl ZonedPatternConfig {
    /// Generate all zones, returning Vec<Vec<CutPath>> indexed by zone.
    /// Each inner Vec contains one CutPath per concentric pass.
    pub fn generate(&self) -> Vec<Vec<CutPath>> {
        self.zones
            .iter()
            .map(|zone| {
                let zone_bounds = Some((zone.inner_radius, zone.outer_radius));
                self.surface.generate_cut(&zone.engine, zone_bounds)
            })
            .collect()
    }
}

impl SurfaceType {
    /// Generate all concentric passes for one zone, returning one CutPath per pass.
    ///
    /// `zone_bounds`: if Some((inner, outer)), points outside that annular ring
    /// are included with z=2.0 (tool lifted).  If None, only workpiece bounds apply.
    pub fn generate_cut(
        &self,
        params: &RoseEngineParams,
        zone_bounds: Option<(f64, f64)>,
    ) -> Vec<CutPath> {
        let num_passes = params.num_passes.max(1) as usize;
        // High resolution: 2000 points per full rotation
        let steps_per_pass = (params.rotations_per_pass * 2000.0).ceil() as usize;

        // Compute effective outer radius from zone or surface
        let outer_r = zone_bounds
            .map(|(_, outer)| outer)
            .unwrap_or_else(|| match self {
                SurfaceType::Circular(c) => c.outer_radius,
                SurfaceType::Rectangular(r) => (r.width.min(r.height)) / 2.0,
            });

        let lobes = params.rosette_lobes as f64;
        let amp = params.amplitude;
        let phase_inc_rad = params.phase_increment.to_radians();

        let crossing = params.crossing_type.to_lowercase();

        // For Moiré: build a second interleaved pass set with +1 lobe
        let is_moire = crossing == "moire";
        let total_logical = if is_moire { num_passes * 2 } else { num_passes };

        let mut paths: Vec<CutPath> = Vec::with_capacity(total_logical);

        for pass_idx in 0..total_logical {
            // For moiré, even indices = primary set, odd indices = secondary set
            let (effective_lobes, logical_i) = if is_moire {
                let set_idx = pass_idx / 2; // which pass within its set
                let extra = (pass_idx % 2) as f64; // 0 or 1 extra lobe
                (lobes + extra, set_idx)
            } else {
                (lobes, pass_idx)
            };

            // Radius for this pass (step inward from outer edge)
            let r_i = outer_r - logical_i as f64 * params.radial_step;
            if r_i <= 0.0 {
                break;
            }

            // Phase for this pass
            let phase_rad: f64 = match crossing.as_str() {
                "none" => 0.0,
                "linear" => logical_i as f64 * phase_inc_rad,
                "moire" => logical_i as f64 * phase_inc_rad,
                "basketweave" => {
                    let bw = params.basketweave_count.max(1) as usize;
                    // Zigzag: 0..bw rising, bw..2bw falling, repeating
                    let cycle = logical_i % (2 * bw);
                    if cycle < bw {
                        cycle as f64 * phase_inc_rad
                    } else {
                        // descending back
                        (2 * bw - cycle) as f64 * phase_inc_rad
                    }
                }
                _ => 0.0, // fallback: no crossing
            };

            let mut points: Vec<Point3D> = Vec::with_capacity(steps_per_pass + 1);

            for step in 0..=steps_per_pass {
                let theta = (step as f64 / steps_per_pass as f64)
                    * 2.0 * PI
                    * params.rotations_per_pass;

                let r = r_i + amp * (effective_lobes * theta + phase_rad).sin();
                let x = r * theta.cos();
                let y = r * theta.sin();

                // Determine z: 0.0 = on surface (cutting), 2.0 = lifted
                let on_surface = self.is_within_bounds(x, y)
                    && self.is_outside_bore(x, y)
                    && zone_bounds
                        .map(|(inner, outer)| {
                            let rr = (x * x + y * y).sqrt();
                            rr >= inner && rr <= outer
                        })
                        .unwrap_or(true);

                let z = if on_surface { 0.0 } else { 2.0 };
                points.push(Point3D { x, y, z });
            }

            paths.push(CutPath { points });
        }

        paths
    }

    /// Is the point (x,y) inside the workpiece boundary?
    pub fn is_within_bounds(&self, x: f64, y: f64) -> bool {
        match self {
            SurfaceType::Circular(c) => {
                let dx = x - c.eccentricity_x;
                let dy = y - c.eccentricity_y;
                (dx * dx + dy * dy).sqrt() <= c.outer_radius
            }
            SurfaceType::Rectangular(r) => {
                x.abs() <= r.width / 2.0 && y.abs() <= r.height / 2.0
            }
        }
    }

    /// Is the point (x,y) outside the bore?
    pub fn is_outside_bore(&self, x: f64, y: f64) -> bool {
        match self {
            SurfaceType::Circular(c) => {
                if c.inner_radius <= 0.0 {
                    return true;
                }
                (x * x + y * y).sqrt() >= c.inner_radius
            }
            SurfaceType::Rectangular(_) => true,
        }
    }

    pub fn thickness(&self) -> f64 {
        match self {
            SurfaceType::Circular(c) => c.thickness,
            SurfaceType::Rectangular(r) => r.thickness,
        }
    }
}
