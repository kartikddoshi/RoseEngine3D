use serde::{Deserialize, Serialize};

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
        let mut paths = Vec::new();
        for i in 0..self.cut_count {
            let effective_amplitude = (self.engine.cam_amplitude
                - (i as f64 * self.engine.radial_step))
                .max(0.0);
            let mut engine_for_cut = self.engine.clone();
            engine_for_cut.cam_amplitude = effective_amplitude;
            let mut cut = self.surface.generate_cut(&engine_for_cut, None);
            let angle = i as f64 * self.cut_angle_offset;
            cut.rotate(angle);
            paths.push(cut);
        }
        paths
    }
}

/// An annular zone on the workpiece with its own pattern parameters.
/// Zone boundaries are measured from the spindle axis (0,0).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PatternZone {
    /// Inner radius of this zone from spindle axis in mm
    pub inner_radius: f64,
    /// Outer radius of this zone from spindle axis in mm
    pub outer_radius: f64,
    pub engine: RoseEngineParams,
    pub cut_count: usize,
    pub cut_angle_offset: f64,
}

/// Multi-zone pattern config — the primary config type for the app.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZonedPatternConfig {
    pub surface: SurfaceType,
    pub zones: Vec<PatternZone>,
}

impl ZonedPatternConfig {
    /// Generate all zones, returning Vec<Vec<CutPath>> indexed by zone.
    pub fn generate(&self) -> Vec<Vec<CutPath>> {
        self.zones
            .iter()
            .map(|zone| {
                let mut paths = Vec::new();
                for i in 0..zone.cut_count {
                    let effective_amplitude = (zone.engine.cam_amplitude
                        - (i as f64 * zone.engine.radial_step))
                        .max(0.0);
                    let mut engine_for_cut = zone.engine.clone();
                    engine_for_cut.cam_amplitude = effective_amplitude;
                    let zone_bounds = Some((zone.inner_radius, zone.outer_radius));
                    let mut cut = self.surface.generate_cut(&engine_for_cut, zone_bounds);
                    let angle = i as f64 * zone.cut_angle_offset;
                    cut.rotate(angle);
                    paths.push(cut);
                }
                paths
            })
            .collect()
    }
}

/// Configuration for a specific Rose Engine Trochoid cut.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoseEngineParams {
    /// Fixed circle radius (R) in mm
    pub fixed_radius: f64,
    /// Rolling circle radius (r) in mm
    pub rolling_radius: f64,
    /// Distance of pen from center of rolling circle (d / amplitude) in mm
    pub cam_amplitude: f64,
    /// Phase shift or offset (theta) in degrees
    pub phase_shift: f64,
    /// Is it rolling outside (Epitrochoid) or inside (Hypotrochoid)?
    pub is_epitrochoid: bool,
    /// Total rotations to calculate (resolution/duration)
    pub rotations: f64,
    /// How much to shrink cam_amplitude between successive cuts (mm units).
    /// 0.0 = pure rotation. 0.05–0.3 = authentic guilloche fill.
    pub radial_step: f64,
}

impl SurfaceType {
    /// Generates a cut path on this surface.
    ///
    /// `zone_bounds`: if Some((inner, outer)), clips points to the annular zone
    /// measured from the spindle origin. The workpiece boundary (incl. eccentricity
    /// and bore) is always applied. If None, only workpiece boundary is applied.
    pub fn generate_cut(
        &self,
        params: &RoseEngineParams,
        zone_bounds: Option<(f64, f64)>,
    ) -> CutPath {
        let mut points = Vec::new();
        // 5 steps per degree for smooth rendering of high-frequency cuts
        let steps = (params.rotations * 360.0 * 5.0) as usize;

        for i in 0..=steps {
            let theta = (i as f64 / 5.0).to_radians();
            let rad_fix = params.fixed_radius;
            let rad_rol = params.rolling_radius;
            let amp = params.cam_amplitude;
            let phase = params.phase_shift.to_radians();

            let t = theta + phase;
            let (x, y) = if params.is_epitrochoid {
                let sum = rad_fix + rad_rol;
                let x = sum * t.cos() - amp * ((sum / rad_rol) * t).cos();
                let y = sum * t.sin() - amp * ((sum / rad_rol) * t).sin();
                (x, y)
            } else {
                let diff = rad_fix - rad_rol;
                let x = diff * t.cos() + amp * ((diff / rad_rol) * t).cos();
                let y = diff * t.sin() - amp * ((diff / rad_rol) * t).sin();
                (x, y)
            };

            // Check all boundary conditions
            let on_surface = self.is_within_bounds(x, y)
                && self.is_outside_bore(x, y)
                && zone_bounds
                    .map(|(inner, outer)| {
                        let r = (x * x + y * y).sqrt();
                        r >= inner && r <= outer
                    })
                    .unwrap_or(true);

            if on_surface {
                // Z = 0.0: surface level (top face of workpiece)
                points.push(Point3D { x, y, z: 0.0 });
            } else {
                // Z = 2.0: safe tool-lift height above surface
                points.push(Point3D { x, y, z: 2.0 });
            }
        }

        CutPath { points }
    }

    /// Is the point (x,y) inside the workpiece boundary?
    /// For circular surfaces this uses the ECCENTRIC workpiece center.
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
    /// The bore is always centered at the spindle origin (0,0).
    pub fn is_outside_bore(&self, x: f64, y: f64) -> bool {
        match self {
            SurfaceType::Circular(c) => {
                if c.inner_radius <= 0.0 {
                    return true; // No bore
                }
                (x * x + y * y).sqrt() >= c.inner_radius
            }
            SurfaceType::Rectangular(_) => true, // No bore concept for rectangular
        }
    }

    pub fn thickness(&self) -> f64 {
        match self {
            SurfaceType::Circular(c) => c.thickness,
            SurfaceType::Rectangular(r) => r.thickness,
        }
    }
}
