# Viewport Alignment, Radial Step & Manufacturing Specs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the misaligned workpiece mesh, add radial progression for authentic guilloche fill, and add a Manufacturing Specs panel with real-world mm dimensions.

**Architecture:** Three independent changes — a one-line viewport fix in PatternCanvas, a Rust struct field + TypeScript mirror for radial step, and a new ManufacturingSpec state object in App with a new UI section in ParameterSidebar. ManufacturingSpec lives as separate App state (not in PatternConfig) because it controls export dimensions, not curve math.

**Tech Stack:** React 19 + TypeScript 5.9, Rust (Tauri 2), Three.js 0.183 via React Three Fiber 9, Tailwind CSS 4, Zustand. No test framework — verification is `tsc -b` (type check), `cargo check` (Rust), and visual confirmation in `npm run tauri dev`.

---

## Verification commands (use throughout)

```bash
# TypeScript type check + build
npm run build

# Rust type check (fast, no link)
cd src-tauri && cargo check && cd ..

# Full dev run
npm run tauri dev
```

---

## Task 1: Fix Viewport — Rotate Workpiece Mesh to Face Camera

**Files:**
- Modify: `src/components/PatternCanvas.tsx`

The cylinder geometry in Three.js defaults to vertical (Y-axis). The camera looks along the Z-axis. Adding `rotation={[Math.PI / 2, 0, 0]}` to the cylinder mesh makes its circular face point toward the camera. Shift camera slightly off-axis for a sense of 3D depth.

**Step 1: Open the file and locate the camera and cylinder**

File: `src/components/PatternCanvas.tsx`

- Camera is at line 16: `camera={{ position: [0, 0, 150], fov: 50 }}`
- Circular cylinder mesh starts at line 76
- Rectangular box mesh starts at line 87
- GridHelper at line 119

**Step 2: Update camera position**

Change line 16 from:
```tsx
camera={{ position: [0, 0, 150], fov: 50 }}
```
To:
```tsx
camera={{ position: [0, 25, 140], fov: 50 }}
```
This tilts the view 10° off-axis so the workpiece reads as a 3D disk rather than a flat square.

**Step 3: Rotate the circular cylinder mesh**

Change the circular mesh (currently around line 76) from:
```tsx
<mesh position={[0, 0, -1]} receiveShadow>
    <cylinderGeometry args={[surface.radius, surface.radius, surface.thickness, 64]} />
```
To:
```tsx
<mesh position={[0, 0, -1]} rotation={[Math.PI / 2, 0, 0]} receiveShadow>
    <cylinderGeometry args={[surface.radius, surface.radius, surface.thickness, 64]} />
```

Three.js cylinders are vertical by default. `rotation={[Math.PI / 2, 0, 0]}` lays the cylinder flat so its circular face aligns with the XY plane where the pattern lives.

**Step 4: Type-check**

```bash
npm run build
```
Expected: Exits with code 0, no TypeScript errors.

**Step 5: Visual verification**

```bash
npm run tauri dev
```
Expected: The workpiece appears as a flat dark disk behind/beneath the gold pattern. The pattern curves sit on the disk face. The view is slightly angled so the disk has visible depth.

**Step 6: Commit**

```bash
git add src/components/PatternCanvas.tsx
git commit -m "fix: rotate cylinder workpiece to face camera, tilt view angle"
```

---

## Task 2: Add Radial Step to Rust Generator

**Files:**
- Modify: `src-tauri/src/generator.rs`

`radial_step` shrinks each successive cut's `cam_amplitude` slightly, so cuts at different radii fill the surface — mimicking the rose engine lathe's slide rest advancing between passes.

**Step 1: Add `radial_step` field to `RoseEngineParams`**

In `src-tauri/src/generator.rs`, the `RoseEngineParams` struct currently ends at `rotations: f64`. Add one field:

```rust
/// How much to shrink cam_amplitude between successive cuts (mm units).
/// 0.0 = pure rotation (current behaviour). 0.1-0.3 = authentic guilloche fill.
pub radial_step: f64,
```

Full struct after change:
```rust
pub struct RoseEngineParams {
    pub fixed_radius: f64,
    pub rolling_radius: f64,
    pub cam_amplitude: f64,
    pub phase_shift: f64,
    pub is_epitrochoid: bool,
    pub rotations: f64,
    pub radial_step: f64,
}
```

**Step 2: Update `PatternConfig::generate()` to apply radial step**

Current `generate()` in `PatternConfig`:
```rust
pub fn generate(&self) -> Vec<CutPath> {
    let mut paths = Vec::new();
    let base_cut = self.surface.generate_cut(&self.engine);

    for i in 0..self.cut_count {
        let angle = i as f64 * self.cut_angle_offset;
        let mut cut = base_cut.clone();
        cut.rotate(angle);
        paths.push(cut);
    }

    paths
}
```

Replace with:
```rust
pub fn generate(&self) -> Vec<CutPath> {
    let mut paths = Vec::new();

    for i in 0..self.cut_count {
        // Each successive cut reduces cam_amplitude by radial_step
        let effective_amplitude = (self.engine.cam_amplitude - (i as f64 * self.engine.radial_step))
            .max(0.0); // Clamp to 0 so cuts don't invert

        let mut engine_for_cut = self.engine.clone();
        engine_for_cut.cam_amplitude = effective_amplitude;

        let mut cut = self.surface.generate_cut(&engine_for_cut);
        let angle = i as f64 * self.cut_angle_offset;
        cut.rotate(angle);
        paths.push(cut);
    }

    paths
}
```

**Step 3: Rust type check**

```bash
cd src-tauri && cargo check && cd ..
```
Expected: `warning: ...` only (hard-link warnings are harmless). No errors.

**Step 4: Commit Rust change**

```bash
git add src-tauri/src/generator.rs
git commit -m "feat(rust): add radial_step to RoseEngineParams for guilloche fill"
```

---

## Task 3: Mirror `radial_step` in TypeScript Types

**Files:**
- Modify: `src/types/generator.ts`

**Step 1: Add `radial_step` to `RoseEngineParams` interface**

In `src/types/generator.ts`, the `RoseEngineParams` interface (line 15–22) currently has:
```typescript
export interface RoseEngineParams {
    fixed_radius: number;
    rolling_radius: number;
    cam_amplitude: number;
    phase_shift: number;
    is_epitrochoid: boolean;
    rotations: number;
}
```

Change to:
```typescript
export interface RoseEngineParams {
    fixed_radius: number;
    rolling_radius: number;
    cam_amplitude: number;
    phase_shift: number;
    is_epitrochoid: boolean;
    rotations: number;
    radial_step: number;
}
```

**Step 2: Add `radial_step` to `initialConfig` in `App.tsx`**

In `src/App.tsx`, `initialConfig` (line 10–22) has an `engine` object. Add `radial_step: 0` to it:

```typescript
const initialConfig: PatternConfig = {
  surface: { type: "Circular", radius: 50, thickness: 2 },
  engine: {
    fixed_radius: 50,
    rolling_radius: 12,
    cam_amplitude: 8,
    phase_shift: 0,
    is_epitrochoid: false,
    rotations: 1,
    radial_step: 0,
  },
  cut_count: 24,
  cut_angle_offset: 15,
};
```

**Step 3: Type-check**

```bash
npm run build
```
Expected: Exits 0. TypeScript will now error anywhere `RoseEngineParams` is constructed without `radial_step` — fix any that appear (presets in `src/data/` likely need updating).

**Step 4: Fix any preset files that construct `RoseEngineParams`**

Check if presets break:
```bash
grep -rn "fixed_radius" src/data/
```

For every preset object in `src/data/presets.ts` and `src/data/extendedPresets.ts` that has a `engine:` block, add `radial_step: 0` to each engine object. This preserves existing behaviour (0 = no radial progression).

**Step 5: Type-check again**

```bash
npm run build
```
Expected: Exits 0.

**Step 6: Commit**

```bash
git add src/types/generator.ts src/App.tsx src/data/
git commit -m "feat(types): add radial_step to RoseEngineParams interface and presets"
```

---

## Task 4: Add Radial Step Slider to Sidebar

**Files:**
- Modify: `src/components/ParameterSidebar.tsx`

**Step 1: Add the slider inside the Pattern Repetition section**

The "Pattern Repetition" section in `ParameterSidebar.tsx` (lines 116–120) currently has two sliders. Add a third:

Current:
```tsx
<div className="space-y-4">
    <h3 className="text-sm uppercase tracking-widest text-zinc-500 font-semibold mb-2">Pattern Repetition</h3>
    <SliderInput label="Cuts (Intersections)" value={config.cut_count} min={1} max={144} step={1} onChange={(v) => setConfig({ ...config, cut_count: v })} />
    <SliderInput label="Angle Offset (deg)" value={config.cut_angle_offset} min={0} max={360} onChange={(v) => setConfig({ ...config, cut_angle_offset: v })} />
</div>
```

Replace with:
```tsx
<div className="space-y-4">
    <h3 className="text-sm uppercase tracking-widest text-zinc-500 font-semibold mb-2">Pattern Repetition</h3>
    <SliderInput label="Cuts (Intersections)" value={config.cut_count} min={1} max={144} step={1} onChange={(v) => setConfig({ ...config, cut_count: v })} />
    <SliderInput label="Angle Offset (deg)" value={config.cut_angle_offset} min={0} max={360} onChange={(v) => setConfig({ ...config, cut_angle_offset: v })} />
    <SliderInput
        label="Radial Step (mm)"
        value={config.engine.radial_step}
        min={0}
        max={2}
        step={0.05}
        onChange={(v) => handleEngineChange("radial_step", v)}
    />
</div>
```

**Step 2: Type-check**

```bash
npm run build
```
Expected: Exits 0.

**Step 3: Visual verification**

```bash
npm run tauri dev
```

- Set Radial Step to 0 → same pattern as before
- Set Radial Step to 0.2 → successive cuts visibly shrink inward, creating dense filled concentric texture (authentic guilloche look)
- Set Radial Step to 0.5 → even more aggressive fill; inner cuts near zero amplitude

**Step 4: Commit**

```bash
git add src/components/ParameterSidebar.tsx
git commit -m "feat(ui): add Radial Step slider for authentic guilloche fill"
```

---

## Task 5: Add `ManufacturingSpec` Type

**Files:**
- Modify: `src/types/generator.ts`

**Step 1: Add the interface**

Append to the end of `src/types/generator.ts`:

```typescript
export interface ManufacturingSpec {
    /** Physical diameter (circular) or width (rectangular) in mm. Range: 10–100. */
    physical_size_mm: number;
    /** Plate thickness in mm. Range: 0.3–3.0. */
    plate_thickness_mm: number;
    /** V-groove cut depth in mm. Range: 0.05–0.45. */
    cut_depth_mm: number;
    /** V-tool included angle in degrees. Standard: 60. Range: 30–90. */
    tool_angle_deg: number;
}

/** Derived from ManufacturingSpec + surface.radius */
export interface ManufacturingDerived {
    /** How many mm one internal unit equals. */
    scale_factor: number;
    /** Width of the V-groove at the surface in mm. */
    groove_width_mm: number;
}

export function deriveManufacturing(spec: ManufacturingSpec, surfaceRadius: number): ManufacturingDerived {
    const scale_factor = spec.physical_size_mm / (2 * surfaceRadius);
    const half_angle_rad = (spec.tool_angle_deg / 2) * (Math.PI / 180);
    const groove_width_mm = 2 * spec.cut_depth_mm / Math.tan(half_angle_rad);
    return { scale_factor, groove_width_mm };
}
```

**Step 2: Type-check**

```bash
npm run build
```
Expected: Exits 0.

**Step 3: Commit**

```bash
git add src/types/generator.ts
git commit -m "feat(types): add ManufacturingSpec interface and deriveManufacturing helper"
```

---

## Task 6: Wire ManufacturingSpec into App State

**Files:**
- Modify: `src/App.tsx`

**Step 1: Import the new types**

At the top of `src/App.tsx`, update the import from `./types/generator`:

```typescript
import type { CutPath, PatternConfig, ManufacturingSpec } from "./types/generator";
```

**Step 2: Add default manufacturing spec constant**

After the `initialConfig` constant (line 22), add:

```typescript
const initialManufacturingSpec: ManufacturingSpec = {
  physical_size_mm: 32,      // 32mm luxury watch dial
  plate_thickness_mm: 0.8,   // Standard watch dial thickness
  cut_depth_mm: 0.30,        // Dramatic engraving depth
  tool_angle_deg: 60,        // Industry-standard V-tool
};
```

**Step 3: Add state in the `App` component**

Inside the `App()` function, after the existing state declarations, add:

```typescript
const [manufacturingSpec, setManufacturingSpec] = useState<ManufacturingSpec>(initialManufacturingSpec);
```

**Step 4: Pass spec to ParameterSidebar**

Update the `<ParameterSidebar>` JSX (around line 188) to pass the new props:

```tsx
<ParameterSidebar
    config={config}
    setConfig={handleConfigChange}
    onGenerate={handleGenerate}
    isGenerating={isGenerating}
    onUndo={handleUndo}
    onRedo={handleRedo}
    onReset={handleReset}
    canUndo={canUndo()}
    canRedo={canRedo()}
    manufacturingSpec={manufacturingSpec}
    setManufacturingSpec={setManufacturingSpec}
/>
```

**Step 5: Type-check**

```bash
npm run build
```
Expected: TypeScript will error that `ParameterSidebar` doesn't accept `manufacturingSpec` prop yet — that's correct, we'll fix it in the next task.

**Step 6: Commit (even with expected TS error, so changes are tracked)**

Skip the build commit here — commit after Task 7 fixes the type error.

---

## Task 7: Add Manufacturing Specs Section to ParameterSidebar

**Files:**
- Modify: `src/components/ParameterSidebar.tsx`

**Step 1: Update `SidebarProps` interface**

At the top of `ParameterSidebar.tsx`, update the imports and props interface:

```typescript
import type { PatternConfig, ManufacturingSpec, deriveManufacturing } from "../types/generator";
```

Wait — `deriveManufacturing` is a function, not a type. Correct import:
```typescript
import type { PatternConfig, ManufacturingSpec } from "../types/generator";
import { deriveManufacturing } from "../types/generator";
```

Update `SidebarProps`:
```typescript
interface SidebarProps {
    config: PatternConfig;
    setConfig: (config: PatternConfig) => void;
    onGenerate: () => void;
    isGenerating: boolean;
    onUndo?: () => void;
    onRedo?: () => void;
    onReset?: () => void;
    canUndo?: boolean;
    canRedo?: boolean;
    manufacturingSpec: ManufacturingSpec;
    setManufacturingSpec: (spec: ManufacturingSpec) => void;
}
```

**Step 2: Destructure the new props**

In the function signature:
```typescript
export function ParameterSidebar({
    config,
    setConfig,
    onGenerate,
    isGenerating,
    onUndo,
    onRedo,
    onReset,
    canUndo = false,
    canRedo = false,
    manufacturingSpec,
    setManufacturingSpec,
}: SidebarProps) {
```

**Step 3: Compute derived values**

At the top of the component body, after the existing handlers, add:

```typescript
const surfaceRadius = config.surface.type === "Circular"
    ? config.surface.radius
    : Math.min((config.surface as any).width, (config.surface as any).height) / 2;

const derived = deriveManufacturing(manufacturingSpec, surfaceRadius);
```

**Step 4: Add the Manufacturing Specs section to the JSX**

In the `<div className="space-y-8 flex-1">` block, **before** the existing Kinematics section, insert a new section. Place it after the `<PresetGallery>` block and its divider:

```tsx
{/* Manufacturing Specifications */}
<div className="space-y-4">
    <h3 className="text-sm uppercase tracking-widest text-zinc-500 font-semibold mb-2">Manufacturing Specs</h3>

    <SliderInput
        label="Physical Size (mm)"
        value={manufacturingSpec.physical_size_mm}
        min={10}
        max={100}
        step={1}
        onChange={(v) => setManufacturingSpec({ ...manufacturingSpec, physical_size_mm: v })}
    />
    <SliderInput
        label="Plate Thickness (mm)"
        value={manufacturingSpec.plate_thickness_mm}
        min={0.3}
        max={3.0}
        step={0.1}
        onChange={(v) => setManufacturingSpec({ ...manufacturingSpec, plate_thickness_mm: v })}
    />
    <SliderInput
        label="Cut Depth (mm)"
        value={manufacturingSpec.cut_depth_mm}
        min={0.05}
        max={0.45}
        step={0.05}
        onChange={(v) => setManufacturingSpec({ ...manufacturingSpec, cut_depth_mm: v })}
    />
    <SliderInput
        label="V-Tool Angle (deg)"
        value={manufacturingSpec.tool_angle_deg}
        min={30}
        max={90}
        step={5}
        onChange={(v) => setManufacturingSpec({ ...manufacturingSpec, tool_angle_deg: v })}
    />

    {/* Derived read-only feedback */}
    <div className="bg-zinc-900/50 rounded-lg border border-zinc-800/50 p-3 space-y-1.5 text-[11px] font-mono">
        <div className="flex justify-between text-zinc-500">
            <span>Scale factor</span>
            <span className="text-zinc-300">1 unit = {derived.scale_factor.toFixed(3)} mm</span>
        </div>
        <div className="flex justify-between text-zinc-500">
            <span>Groove width</span>
            <span className="text-zinc-300">{derived.groove_width_mm.toFixed(3)} mm</span>
        </div>
    </div>
</div>

<div className="w-full h-px bg-gradient-to-r from-transparent via-zinc-800 to-transparent"></div>
```

**Step 5: Type-check**

```bash
npm run build
```
Expected: Exits 0, no TypeScript errors.

**Step 6: Visual verification**

```bash
npm run tauri dev
```

Expected in sidebar:
- New "Manufacturing Specs" section visible above Kinematics
- Physical Size slider defaults to 32mm
- "Scale factor: 1 unit = 0.320 mm" shown (32mm / (2 × 50 units))
- "Groove width: X.XXX mm" updates live as cut depth or tool angle changes
- Adjusting Physical Size updates scale factor in real-time

**Step 7: Commit**

```bash
git add src/components/ParameterSidebar.tsx src/App.tsx src/types/generator.ts
git commit -m "feat: add Manufacturing Specs panel with mm dimensions and derived groove geometry"
```

---

## Task 8: Final Integration Verification

**Step 1: Full build check**

```bash
npm run build
```
Expected: Exits 0.

**Step 2: Rust check**

```bash
cd src-tauri && cargo check && cd ..
```
Expected: Only hard-link warnings, no errors.

**Step 3: End-to-end visual test**

```bash
npm run tauri dev
```

Verify all three fixes together:

| Check | Expected |
|---|---|
| Workpiece shape | Flat disk visible, not a horizontal bar |
| Pattern position | Gold curves sit on the disk face |
| Radial Step = 0 | Single-radius spirograph look (baseline) |
| Radial Step = 0.2 | Dense filled concentric guilloche texture |
| Manufacturing panel | Shows in sidebar, sliders work, scale factor updates |
| Default values | 32mm, 0.8mm, 0.30mm, 60° |
| Presets still work | Selecting a preset generates pattern correctly |
| Export buttons | SVG Pattern / Config JSON / Data JSON still work |

**Step 4: Final commit if any cleanup needed**

```bash
git add -p
git commit -m "fix: final integration cleanup for viewport, radial step, manufacturing specs"
```

---

## Summary of All Files Changed

| File | Change |
|---|---|
| `src/components/PatternCanvas.tsx` | Camera tilt, cylinder rotation |
| `src-tauri/src/generator.rs` | `radial_step` field + generate() logic |
| `src/types/generator.ts` | `radial_step` in interface, `ManufacturingSpec`, `deriveManufacturing` |
| `src/App.tsx` | `initialManufacturingSpec`, `manufacturingSpec` state, pass to sidebar |
| `src/components/ParameterSidebar.tsx` | Radial Step slider, Manufacturing Specs section |
| `src/data/presets.ts` | Add `radial_step: 0` to each engine object |
| `src/data/extendedPresets.ts` | Add `radial_step: 0` to each engine object |
