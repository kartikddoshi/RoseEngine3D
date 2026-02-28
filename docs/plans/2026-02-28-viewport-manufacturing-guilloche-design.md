# Design: Viewport Alignment, Manufacturing Specs & Guilloche Authenticity

**Date:** 2026-02-28
**Status:** Approved
**Scope:** Three self-contained fixes to make the Rose Engine app visually correct and manufacturing-ready

---

## Background

The app renders correctly after the postprocessing crash fix. Three issues remain before the app is useful:

1. The workpiece mesh is oriented wrong — cylinder appears as a horizontal bar instead of a flat disk
2. No real-world mm dimensions — all parameters are unitless, nothing maps to physical manufacturing specs
3. Cuts are all at the same radius — looks like a single spirograph rather than filled guilloche texture

---

## Fix 1: Viewport Alignment

### Problem
`cylinderGeometry` in Three.js defaults to vertical orientation (Y-axis up). The camera sits at `[0, 0, 150]` looking along the Z-axis. Result: the circular workpiece appears as a thin horizontal bar across the center of the screen rather than a flat disk with the pattern sitting on top of it.

### Solution
- Rotate the cylinder mesh `Math.PI / 2` around the X-axis so its circular face points toward the camera
- Adjust camera to a slight top-down angle (`[0, 20, 140]` instead of `[0, 0, 150]`) to give a sense of 3D depth
- Keep the pattern grid helper aligned with the surface

### Files Changed
- `src/components/PatternCanvas.tsx` — cylinder rotation + camera position

---

## Fix 2: Manufacturing Specifications Panel

### Problem
The app has no concept of physical size. `fixed_radius: 50` means 50 internal units — never mapped to mm. There is no way to specify "I want a 32mm watch dial with 0.8mm plate thickness and 0.3mm cut depth."

### Manufacturing Size Range
Based on traditional guilloche use cases and the reference project (Guilloche3D caps at 100mm):

| Use Case | Diameter / Size |
|---|---|
| Watch crown face | 8–12mm |
| Watch dial (standard) | 25–40mm |
| Cufflink face | 15–20mm |
| Pendant / brooch | 20–35mm |
| Currency / document plate | 50–100mm |

- **Minimum supported:** 10mm diameter
- **Maximum supported:** 100mm (reference project hard cap)
- **Default:** 32mm diameter × 0.8mm thick (luxury watch dial standard)

### Parameters to Expose

| Parameter | Range | Default | Notes |
|---|---|---|---|
| Physical diameter (circular) | 10–100mm | 32mm | Maps radius units → mm |
| Physical width/height (rect) | 10×10 – 100×100mm | 32×32mm | |
| Plate thickness | 0.3–3.0mm | 0.8mm | Traditional watch dial |
| Cut depth | 0.05–0.45mm | 0.30mm | 0.3–0.45mm = dramatic engraving |
| V-tool angle | 30°–90° | 60° | Industry standard |

### Scale Factor
A `scale_factor` is derived automatically:

```
scale_factor = physical_diameter_mm / (2 * fixed_radius_units)
```

This is passed alongside the pattern config so exports and future STL generation use real mm coordinates. The Rust generator stays unit-agnostic; scaling happens at the boundary.

### UI Placement
New collapsible section in `ParameterSidebar.tsx` labeled **"Manufacturing Specs"**, placed above the existing Kinematics section. Shows computed values (groove width from V-tool geometry) as read-only feedback.

### Files Changed
- `src/components/ParameterSidebar.tsx` — new Manufacturing Specs section
- `src/types/generator.ts` — add `ManufacturingSpec` interface
- `src/App.tsx` — pass manufacturing spec through to export panel

---

## Fix 3: Radial Progression (Authentic Guilloche Fill)

### Problem
All cuts in the current implementation rotate around the Z-axis but trace the **same radius**. A real rose engine lathe advances the tool slightly inward between passes, building up dense overlapping concentric layers of grooves that fill the workpiece surface. Without this, the output looks like a single spirograph outline rather than a filled guilloche texture.

### Real Rose Engine Behaviour
On a physical rose engine:
1. The operator sets the rosette (controls the waveform shape and lobe count)
2. Makes a pass — the tool traces one full revolution cutting a groove
3. Advances the slide rest by a small amount (0.1–0.3mm typically)
4. Makes another pass at the new radius
5. Repeats until the full workpiece surface is filled

The result is concentric offset curves — all sharing the same waveform but at progressively smaller radii — that interleave and create the characteristic dense texture.

### Solution
Add a `radial_step` parameter to `RoseEngineParams` in Rust. When non-zero, each successive cut scales the tracing amplitude `d` (cam_amplitude) slightly, simulating the tool advancing inward. The pattern generator produces `cut_count` cuts each at a different effective amplitude.

```
cut[i].cam_amplitude = cam_amplitude - (i * radial_step)
```

This is mathematically equivalent to the lathe's slide rest advance because the trochoid's radial extent is directly controlled by `cam_amplitude`.

### Parameters

| Parameter | Range | Default | Notes |
|---|---|---|---|
| Radial step (mm) | 0.0–2.0 | 0.0 | 0 = current behaviour (pure rotation) |
| | | | 0.1–0.3 = authentic guilloche fill |

When `radial_step > 0`, the `cut_angle_offset` continues to apply rotation between passes so the two motions combine: each successive cut is both rotated AND at a slightly different radius, exactly matching real lathe kinematics.

### UI Placement
New slider in `ParameterSidebar.tsx` within the Kinematics section, below the existing Cut Count / Angle Offset controls. Labelled **"Radial Step (mm)"** with a tooltip explaining the lathe analogy.

### Files Changed
- `src-tauri/src/generator.rs` — add `radial_step` field, modify `generate()` to apply it
- `src/types/generator.ts` — mirror `radial_step` in `RoseEngineParams`
- `src/components/ParameterSidebar.tsx` — new Radial Step slider

---

## Implementation Order

These three fixes are independent and can be sequenced as:

1. **Fix 1** (Viewport) — smallest change, immediate visual payoff, confirms rendering is correct before adding more parameters
2. **Fix 3** (Radial step) — Rust + TS type change, no UI complexity
3. **Fix 2** (Manufacturing specs) — largest UI change, builds on confirmed working viewport

---

## Success Criteria

- [ ] The circular workpiece appears as a flat disk with the gold pattern sitting on its face
- [ ] Manufacturing Specs panel exists with diameter, thickness, cut depth, V-tool angle
- [ ] Default values produce a 32mm × 0.8mm watch dial configuration
- [ ] Scale factor is computed and visible (e.g. "1 unit = 0.32mm")
- [ ] Radial step slider at 0.2mm produces visibly denser, filled guilloche texture vs 0.0mm
- [ ] All existing pattern generation and export functionality continues to work
