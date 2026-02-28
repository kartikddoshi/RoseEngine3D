import type { PatternType } from "../types/generator";

export interface ExtendedPreset {
  id: string;
  name: string;
  description: string;
  patternType: string; // "trochoid", "rose", "lissajous", "spiral"
  pattern: PatternType;
  cutCount: number;
  cutAngleOffset: number;
}

export const extendedPresets: ExtendedPreset[] = [
  // Rose Curve Presets
  {
    id: "rose-5-petal",
    name: "5-Petal Rose",
    description: "Classic five-petal flower",
    patternType: "rose",
    pattern: {
      pattern_type: "RoseCurve",
      k: 5,
      amplitude: 45,
      rotations: 10,
    },
    cutCount: 24,
    cutAngleOffset: 15,
  },
  {
    id: "rose-7-petal",
    name: "7-Petal Rose",
    description: "Elegant seven-petal design",
    patternType: "rose",
    pattern: {
      pattern_type: "RoseCurve",
      k: 7,
      amplitude: 40,
      rotations: 14,
    },
    cutCount: 28,
    cutAngleOffset: 12.86,
  },
  {
    id: "rose-fractional",
    name: "Fractional Rose",
    description: "Complex fractional k value",
    patternType: "rose",
    pattern: {
      pattern_type: "RoseCurve",
      k: 3.5,
      amplitude: 50,
      rotations: 20,
    },
    cutCount: 24,
    cutAngleOffset: 15,
  },

  // Lissajous Presets
  {
    id: "lissajous-3-2",
    name: "Lissajous 3:2",
    description: "Classic 3:2 frequency ratio",
    patternType: "lissajous",
    pattern: {
      pattern_type: "Lissajous",
      freq_x: 3,
      freq_y: 2,
      phase: 90,
      amp_x: 45,
      amp_y: 45,
      rotations: 20,
    },
    cutCount: 18,
    cutAngleOffset: 20,
  },
  {
    id: "lissajous-5-4",
    name: "Lissajous 5:4",
    description: "Complex 5:4 pattern",
    patternType: "lissajous",
    pattern: {
      pattern_type: "Lissajous",
      freq_x: 5,
      freq_y: 4,
      phase: 0,
      amp_x: 50,
      amp_y: 50,
      rotations: 20,
    },
    cutCount: 24,
    cutAngleOffset: 15,
  },
  {
    id: "lissajous-butterfly",
    name: "Butterfly",
    description: "Butterfly-shaped lissajous",
    patternType: "lissajous",
    pattern: {
      pattern_type: "Lissajous",
      freq_x: 2,
      freq_y: 3,
      phase: 45,
      amp_x: 50,
      amp_y: 40,
      rotations: 15,
    },
    cutCount: 12,
    cutAngleOffset: 30,
  },

  // Spiral Presets
  {
    id: "spiral-archimedean",
    name: "Archimedean Spiral",
    description: "Classic uniform spiral",
    patternType: "spiral",
    pattern: {
      pattern_type: "Spiral",
      spiral_type: "Archimedean",
      a: 5,
      b: 2,
      rotations: 5,
    },
    cutCount: 12,
    cutAngleOffset: 30,
  },
  {
    id: "spiral-logarithmic",
    name: "Logarithmic Spiral",
    description: "Golden ratio spiral",
    patternType: "spiral",
    pattern: {
      pattern_type: "Spiral",
      spiral_type: "Logarithmic",
      a: 3,
      b: 0.2,
      rotations: 4,
    },
    cutCount: 8,
    cutAngleOffset: 45,
  },
  {
    id: "spiral-dense",
    name: "Dense Spiral Texture",
    description: "Tight spiral pattern",
    patternType: "spiral",
    pattern: {
      pattern_type: "Spiral",
      spiral_type: "Archimedean",
      a: 2,
      b: 1.5,
      rotations: 8,
    },
    cutCount: 36,
    cutAngleOffset: 10,
  },

  // Hybrid/Mixed Presets
  {
    id: "rose-starburst",
    name: "Rose Starburst",
    description: "12-point rose star",
    patternType: "rose",
    pattern: {
      pattern_type: "RoseCurve",
      k: 12,
      amplitude: 35,
      rotations: 24,
    },
    cutCount: 48,
    cutAngleOffset: 7.5,
  },
  {
    id: "lissajous-web",
    name: "Web Pattern",
    description: "Intricate web-like structure",
    patternType: "lissajous",
    pattern: {
      pattern_type: "Lissajous",
      freq_x: 7,
      freq_y: 5,
      phase: 30,
      amp_x: 48,
      amp_y: 48,
      rotations: 25,
    },
    cutCount: 36,
    cutAngleOffset: 10,
  },
];

// Helper function to get presets by type
export function getPresetsByType(type: string): ExtendedPreset[] {
  return extendedPresets.filter((preset) => preset.patternType === type);
}

// Helper function to get default parameters for each pattern type
export function getDefaultPatternParams(
  type: string
): PatternType {
  switch (type) {
    case "trochoid":
      return {
        pattern_type: "Trochoid",
        fixed_radius: 50,
        rolling_radius: 12,
        cam_amplitude: 8,
        phase_shift: 0,
        is_epitrochoid: false,
        rotations: 1,
      };
    case "rose":
      return {
        pattern_type: "RoseCurve",
        k: 5,
        amplitude: 45,
        rotations: 10,
      };
    case "lissajous":
      return {
        pattern_type: "Lissajous",
        freq_x: 3,
        freq_y: 2,
        phase: 90,
        amp_x: 45,
        amp_y: 45,
        rotations: 20,
      };
    case "spiral":
      return {
        pattern_type: "Spiral",
        spiral_type: "Archimedean",
        a: 5,
        b: 2,
        rotations: 5,
      };
    default:
      return getDefaultPatternParams("trochoid");
  }
}
