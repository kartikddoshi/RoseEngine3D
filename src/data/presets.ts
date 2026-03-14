import type { ZonedPatternConfig, RoseEngineParams } from "../types/generator";

export interface Preset {
  id: string;
  name: string;
  description: string;
  config: ZonedPatternConfig;
  thumbnail?: string;
}

// Standard 32 mm watch dial surface (no bore, centred)
const DEFAULT_SURFACE: ZonedPatternConfig["surface"] = {
  type: "Circular",
  outer_radius: 16,
  inner_radius: 0,
  thickness: 0.8,
  eccentricity_x: 0,
  eccentricity_y: 0,
};

function makeZone(
  inner: number,
  outer: number,
  engine: RoseEngineParams,
  color = "#d4af37",
  label = "Main",
): ZonedPatternConfig["zones"][number] {
  return {
    inner_radius: inner,
    outer_radius: outer,
    engine,
    cut_count: 1,
    cut_angle_offset: 0,
    color,
    label,
  };
}

function single(engine: RoseEngineParams, color = "#d4af37"): ZonedPatternConfig {
  return {
    surface: DEFAULT_SURFACE,
    zones: [makeZone(2, 16, engine, color, "Main")],
  };
}

export const presets: Preset[] = [
  // ─── 1. Vague de Genève (Geneva Waves) ───────────────────────────────────────
  {
    id: "vague-de-geneve",
    name: "Vague de Genève",
    description:
      "Classic Geneva waves: 6-lobe rosette, no crossing — pure concentric sinusoidal rings with hypnotic depth.",
    config: single({
      rosette_lobes: 6,
      amplitude: 0.5,
      num_passes: 60,
      radial_step: 0.23,
      crossing_type: "none",
      phase_increment: 0,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#c0c0c0"),
  },

  // ─── 2. Grain d'Orge (Barleycorn) ─────────────────────────────────────────
  {
    id: "grain-d-orge",
    name: "Grain d'Orge",
    description:
      "Barleycorn: 8-lobe rosette with linear phase crossing at 7.5° per pass. The signature Swiss watchmaking finish.",
    config: single({
      rosette_lobes: 8,
      amplitude: 0.4,
      num_passes: 50,
      radial_step: 0.28,
      crossing_type: "linear",
      phase_increment: 7.5,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }),
  },

  // ─── 3. Panier (Basketweave) ─────────────────────────────────────────────
  {
    id: "panier",
    name: "Panier",
    description:
      "Basketweave guilloché: 6-lobe rosette with zigzag phase reversal every 6 passes — creates a woven textile illusion.",
    config: single({
      rosette_lobes: 6,
      amplitude: 0.45,
      num_passes: 60,
      radial_step: 0.23,
      crossing_type: "basketweave",
      phase_increment: 10,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#b87333"),
  },

  // ─── 4. Soleil Rayonnant (Radial Sunburst) ─────────────────────────────────
  {
    id: "soleil-rayonnant",
    name: "Soleil Rayonnant",
    description:
      "Radiant sunburst: 72-lobe rosette at tiny amplitude, no crossing — dense radial lines that shimmer like sunrays.",
    config: single({
      rosette_lobes: 72,
      amplitude: 0.12,
      num_passes: 40,
      radial_step: 0.35,
      crossing_type: "none",
      phase_increment: 0,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#d4af37"),
  },

  // ─── 5. Flinqué Diamant ──────────────────────────────────────────────────
  {
    id: "flinque-diamant",
    name: "Flinqué Diamant",
    description:
      "Diamond flinqué: 4-lobe rosette with large 30° linear crossing — creates overlapping leaf-diamond shapes.",
    config: single({
      rosette_lobes: 4,
      amplitude: 0.6,
      num_passes: 40,
      radial_step: 0.35,
      crossing_type: "linear",
      phase_increment: 30,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#d4af37"),
  },

  // ─── 6. Moiré Hypnotique ────────────────────────────────────────────────
  {
    id: "moire-hypnotique",
    name: "Moiré Hypnotique",
    description:
      "Moiré interference: two interleaved wave sets with 8 lobes and 9 lobes, creating hypnotic interference bands.",
    config: single({
      rosette_lobes: 8,
      amplitude: 0.35,
      num_passes: 50,
      radial_step: 0.14,  // tighter — two interleaved sets effectively halve the spacing
      crossing_type: "moire",
      phase_increment: 5,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#c0c0c0"),
  },

  // ─── 7. Vague Spirale (Spiral Waves) ──────────────────────────────────────
  {
    id: "vague-spirale",
    name: "Vague Spirale",
    description:
      "Spiral waves: 8-lobe rosette with steeper 15° linear crossing — the coincidence points spiral inward.",
    config: single({
      rosette_lobes: 8,
      amplitude: 0.4,
      num_passes: 50,
      radial_step: 0.28,
      crossing_type: "linear",
      phase_increment: 15,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#d4af37"),
  },

  // ─── 8. Clous de Paris (Fine Hobnail) ─────────────────────────────────────
  {
    id: "clous-de-paris",
    name: "Clous de Paris",
    description:
      "Fine hobnail texture: 24-lobe rosette at tiny amplitude, no crossing — dense fine-grained pyramid texture.",
    config: single({
      rosette_lobes: 24,
      amplitude: 0.15,
      num_passes: 80,
      radial_step: 0.175,
      crossing_type: "none",
      phase_increment: 0,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#c0c0c0"),
  },

  // ─── 9. Flamme (Flame) ───────────────────────────────────────────────────
  {
    id: "flamme",
    name: "Flamme",
    description:
      "Flame guilloché: 3-lobe rosette with large 20° linear crossing and 0.7 mm amplitude — bold flame tendrils.",
    config: single({
      rosette_lobes: 3,
      amplitude: 0.7,
      num_passes: 40,
      radial_step: 0.35,
      crossing_type: "linear",
      phase_increment: 20,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }, "#b87333"),
  },

  // ─── 10. Breguet Classique ─────────────────────────────────────────────────
  {
    id: "breguet-classique",
    name: "Breguet Classique",
    description:
      "Classic Breguet guilloché: 12-lobe rosette with fine 5° crossing, 70 passes, 0.3 mm amplitude — formal and refined.",
    config: single({
      rosette_lobes: 12,
      amplitude: 0.3,
      num_passes: 70,
      radial_step: 0.20,
      crossing_type: "linear",
      phase_increment: 5,
      basketweave_count: 6,
      rotations_per_pass: 1.0,
    }),
  },

  // ─── 11. Atelier Wen Inspired (Multi-zone) ────────────────────────────────
  {
    id: "atelier-wen",
    name: "Atelier Wen Inspired",
    description:
      "Multi-zone: concentric waves in the inner zone, barleycorn in the outer — inspired by Chinese-Swiss fusion dial design.",
    config: {
      surface: DEFAULT_SURFACE,
      zones: [
        makeZone(2, 8, {
          rosette_lobes: 6,
          amplitude: 0.45,
          num_passes: 30,
          radial_step: 0.2,
          crossing_type: "none",
          phase_increment: 0,
          basketweave_count: 6,
          rotations_per_pass: 1.0,
        }, "#c0c0c0", "Inner — Concentric"),
        makeZone(8, 16, {
          rosette_lobes: 8,
          amplitude: 0.35,
          num_passes: 40,
          radial_step: 0.2,
          crossing_type: "linear",
          phase_increment: 7.5,
          basketweave_count: 6,
          rotations_per_pass: 1.0,
        }, "#d4af37", "Outer — Barleycorn"),
      ],
    },
  },

  // ─── 12. Double Zone Luxe ─────────────────────────────────────────────────
  {
    id: "double-zone-luxe",
    name: "Double Zone Luxe",
    description:
      "Luxury double zone: basketweave inside, barleycorn outside — contrasting textures in a single dial.",
    config: {
      surface: DEFAULT_SURFACE,
      zones: [
        makeZone(2, 8, {
          rosette_lobes: 6,
          amplitude: 0.4,
          num_passes: 30,
          radial_step: 0.2,
          crossing_type: "basketweave",
          phase_increment: 10,
          basketweave_count: 5,
          rotations_per_pass: 1.0,
        }, "#b87333", "Inner — Basketweave"),
        makeZone(8, 16, {
          rosette_lobes: 8,
          amplitude: 0.35,
          num_passes: 40,
          radial_step: 0.2,
          crossing_type: "linear",
          phase_increment: 7.5,
          basketweave_count: 6,
          rotations_per_pass: 1.0,
        }, "#d4af37", "Outer — Barleycorn"),
      ],
    },
  },
];
