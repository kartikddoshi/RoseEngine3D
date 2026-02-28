import type { ZonedPatternConfig } from "../types/generator";

export interface Preset {
  id: string;
  name: string;
  description: string;
  config: ZonedPatternConfig;
  thumbnail?: string;
}

// Default surface for all single-zone presets: 32mm dial, 0.8mm thick, no bore, centred
const DEFAULT_SURFACE: ZonedPatternConfig["surface"] = {
  type: "Circular",
  outer_radius: 16,
  inner_radius: 0,
  thickness: 0.8,
  eccentricity_x: 0,
  eccentricity_y: 0,
};

// Wrap legacy engine params (originally in 50-unit abstract space)
// into a single-zone ZonedPatternConfig scaled to 16mm (x0.32).
function singleZone(
  engine: { fixed_radius: number; rolling_radius: number; cam_amplitude: number;
            phase_shift: number; is_epitrochoid: boolean; rotations: number },
  cut_count: number,
  cut_angle_offset: number,
  color = "#d4af37",
): ZonedPatternConfig {
  const S = 0.32; // 16mm / 50 abstract units
  return {
    surface: DEFAULT_SURFACE,
    zones: [{
      inner_radius: 0,
      outer_radius: 16,
      engine: {
        fixed_radius:   engine.fixed_radius   * S,
        rolling_radius: engine.rolling_radius * S,
        cam_amplitude:  engine.cam_amplitude  * S,
        phase_shift:    engine.phase_shift,
        is_epitrochoid: engine.is_epitrochoid,
        rotations:      engine.rotations,
        radial_step:    0,
      },
      cut_count,
      cut_angle_offset,
      color,
      label: "Main Zone",
    }],
  };
}

export const presets: Preset[] = [
  {
    id: "classic-5-petal",
    name: "Classic 5-Petal Rose",
    description: "Traditional watch dial pattern with 5 symmetric petals",
    config: singleZone(
      { fixed_radius:50, rolling_radius:10, cam_amplitude:8, phase_shift:0, is_epitrochoid:false, rotations:1 },
      24, 15
    ),
  },
  {
    id: "flower-7-petal",
    name: "Seven-Petal Flower",
    description: "Elegant 7-petal floral design",
    config: singleZone(
      { fixed_radius:50, rolling_radius:7.14, cam_amplitude:12, phase_shift:0, is_epitrochoid:false, rotations:1 },
      36, 10
    ),
  },
  {
    id: "basketweave",
    name: "Basketweave",
    description: "Complex interwoven design for luxury dials",
    config: singleZone(
      { fixed_radius:45, rolling_radius:15, cam_amplitude:20, phase_shift:45, is_epitrochoid:true, rotations:2 },
      48, 7.5, "#b87333"
    ),
  },
  {
    id: "sunburst",
    name: "Sunburst",
    description: "Radial sunburst pattern with fine details",
    config: singleZone(
      { fixed_radius:50, rolling_radius:25, cam_amplitude:5, phase_shift:0, is_epitrochoid:false, rotations:1 },
      72, 5
    ),
  },
  {
    id: "moire-wave",
    name: "Moire Wave",
    description: "Hypnotic moire interference pattern",
    config: singleZone(
      { fixed_radius:48, rolling_radius:12, cam_amplitude:15, phase_shift:90, is_epitrochoid:true, rotations:3 },
      24, 15, "#c0c0c0"
    ),
  },
  {
    id: "delicate-loops",
    name: "Delicate Loops",
    description: "Fine looping pattern with precise detail",
    config: singleZone(
      { fixed_radius:50, rolling_radius:20, cam_amplitude:25, phase_shift:0, is_epitrochoid:false, rotations:1.5 },
      18, 20
    ),
  },
  {
    id: "star-burst-12",
    name: "12-Point Star",
    description: "Sharp 12-point starburst design",
    config: singleZone(
      { fixed_radius:50, rolling_radius:4.17, cam_amplitude:6, phase_shift:0, is_epitrochoid:false, rotations:1 },
      48, 7.5
    ),
  },
  {
    id: "classic-guilloche",
    name: "Classic Guilloche",
    description: "Traditional Swiss watchmaking pattern",
    config: singleZone(
      { fixed_radius:50, rolling_radius:12, cam_amplitude:8, phase_shift:0, is_epitrochoid:false, rotations:1 },
      24, 15
    ),
  },
  {
    id: "ornate-web",
    name: "Ornate Web",
    description: "Intricate web-like structure",
    config: singleZone(
      { fixed_radius:45, rolling_radius:18, cam_amplitude:22, phase_shift:30, is_epitrochoid:true, rotations:2.5 },
      36, 10, "#c0c0c0"
    ),
  },
  {
    id: "fine-texture",
    name: "Fine Texture",
    description: "Dense textured pattern for subtle backgrounds",
    config: singleZone(
      { fixed_radius:50, rolling_radius:8, cam_amplitude:3, phase_shift:0, is_epitrochoid:false, rotations:1 },
      96, 3.75
    ),
  },
  {
    id: "dramatic-waves",
    name: "Dramatic Waves",
    description: "Bold wave pattern with strong visual impact",
    config: singleZone(
      { fixed_radius:50, rolling_radius:15, cam_amplitude:30, phase_shift:0, is_epitrochoid:true, rotations:2 },
      12, 30, "#b87333"
    ),
  },
  {
    id: "celtic-knot",
    name: "Celtic Knot",
    description: "Interlaced pattern inspired by Celtic art",
    config: singleZone(
      { fixed_radius:48, rolling_radius:16, cam_amplitude:18, phase_shift:60, is_epitrochoid:false, rotations:3 },
      24, 15
    ),
  },
];
