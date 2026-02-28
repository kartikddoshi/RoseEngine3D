// ---------------------------------------------------------------------------
// Surface types
// ---------------------------------------------------------------------------

export type SurfaceType =
    | {
          type: "Circular";
          /** Outer radius of the workpiece in mm */
          outer_radius: number;
          /** Bore (inner hole) radius in mm. 0 = solid disk. */
          inner_radius: number;
          /** Plate thickness in mm */
          thickness: number;
          /** Workpiece center offset from spindle axis X (mm) */
          eccentricity_x: number;
          /** Workpiece center offset from spindle axis Y (mm) */
          eccentricity_y: number;
      }
    | { type: "Rectangular"; width: number; height: number; thickness: number };

// ---------------------------------------------------------------------------
// Path types
// ---------------------------------------------------------------------------

export interface Point3D {
    x: number;
    y: number;
    z: number;
}

export interface CutPath {
    points: Point3D[];
}

// ---------------------------------------------------------------------------
// Rose engine parameters
// ---------------------------------------------------------------------------

export interface RoseEngineParams {
    /** Fixed circle radius R (mm) */
    fixed_radius: number;
    /** Rolling circle radius r (mm) */
    rolling_radius: number;
    /** Cam follower amplitude d (mm) */
    cam_amplitude: number;
    /** Phase shift in degrees */
    phase_shift: number;
    /** true = epitrochoid (rolling outside), false = hypotrochoid (rolling inside) */
    is_epitrochoid: boolean;
    /** Number of full curve rotations to compute */
    rotations: number;
    /** Amplitude reduction per successive cut (mm). 0 = pure rotation. */
    radial_step: number;
}

// ---------------------------------------------------------------------------
// Pattern zone
// ---------------------------------------------------------------------------

export interface PatternZone {
    /** Inner radius of this zone from spindle axis (mm) */
    inner_radius: number;
    /** Outer radius of this zone from spindle axis (mm) */
    outer_radius: number;
    engine: RoseEngineParams;
    cut_count: number;
    cut_angle_offset: number;
    /** Hex color for 3D visualization */
    color: string;
    /** Display label */
    label: string;
}

// ---------------------------------------------------------------------------
// Config types
// ---------------------------------------------------------------------------

/** Primary multi-zone config used by the app */
export interface ZonedPatternConfig {
    surface: SurfaceType;
    zones: PatternZone[];
}

/** Legacy single-zone config — kept for export commands */
export interface PatternConfig {
    surface: SurfaceType;
    engine: RoseEngineParams;
    cut_count: number;
    cut_angle_offset: number;
}

// Extended pattern types (Phase 2)
export type PatternType =
    | { pattern_type: "Trochoid"; fixed_radius: number; rolling_radius: number; cam_amplitude: number; phase_shift: number; is_epitrochoid: boolean; rotations: number; }
    | { pattern_type: "RoseCurve"; k: number; amplitude: number; rotations: number; }
    | { pattern_type: "Lissajous"; freq_x: number; freq_y: number; phase: number; amp_x: number; amp_y: number; rotations: number; }
    | { pattern_type: "Spiral"; spiral_type: "Archimedean" | "Logarithmic"; a: number; b: number; rotations: number; };

export interface ExtendedPatternConfig {
    surface: SurfaceType;
    pattern: PatternType;
    cut_count: number;
    cut_angle_offset: number;
}

// ---------------------------------------------------------------------------
// Manufacturing specification
// ---------------------------------------------------------------------------

export interface ManufacturingSpec {
    /** Physical diameter in mm → outer_radius = /2 */
    physical_size_mm: number;
    /** Bore diameter in mm → inner_radius = /2 */
    bore_size_mm: number;
    /** Plate thickness in mm */
    plate_thickness_mm: number;
    /** V-groove cut depth in mm */
    cut_depth_mm: number;
    /** V-tool included angle in degrees */
    tool_angle_deg: number;
    /** Workpiece center offset from spindle (X) in mm */
    eccentricity_x_mm: number;
    /** Workpiece center offset from spindle (Y) in mm */
    eccentricity_y_mm: number;
}

export interface ManufacturingDerived {
    /** Width of the V-groove at the surface in mm */
    groove_width_mm: number;
}

/** Derive the SurfaceType directly from manufacturing spec (mm-native) */
export function specToSurface(spec: ManufacturingSpec): Extract<SurfaceType, { type: "Circular" }> {
    return {
        type: "Circular",
        outer_radius: spec.physical_size_mm / 2,
        inner_radius: spec.bore_size_mm / 2,
        thickness: spec.plate_thickness_mm,
        eccentricity_x: spec.eccentricity_x_mm,
        eccentricity_y: spec.eccentricity_y_mm,
    };
}

export function deriveManufacturing(spec: ManufacturingSpec): ManufacturingDerived {
    const half_angle_rad = (spec.tool_angle_deg / 2) * (Math.PI / 180);
    const groove_width_mm = 2 * spec.cut_depth_mm / Math.tan(half_angle_rad);
    return { groove_width_mm };
}
