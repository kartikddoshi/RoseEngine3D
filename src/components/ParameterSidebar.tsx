import { useState } from "react";
import type { ZonedPatternConfig, ManufacturingSpec, PatternZone, RoseEngineParams } from "../types/generator";
import { deriveManufacturing } from "../types/generator";
import { PresetGallery } from "./PresetGallery";

interface SidebarProps {
    config: ZonedPatternConfig;
    setConfig: (config: ZonedPatternConfig) => void;
    onGenerate: () => void;
    isGenerating: boolean;
    onUndo: () => void;
    onRedo: () => void;
    onReset: () => void;
    canUndo: boolean;
    canRedo: boolean;
    manufacturingSpec: ManufacturingSpec;
    setManufacturingSpec: (spec: ManufacturingSpec) => void;
}

const ZONE_COLORS = [
    { label: "Gold",   value: "#d4af37" },
    { label: "Silver", value: "#c0c0c0" },
    { label: "Copper", value: "#b87333" },
    { label: "Cyan",   value: "#00bcd4" },
];

export function ParameterSidebar({
    config,
    setConfig,
    onGenerate,
    isGenerating,
    onUndo,
    onRedo,
    onReset,
    canUndo,
    canRedo,
    manufacturingSpec,
    setManufacturingSpec,
}: SidebarProps) {
    const [expandedZones, setExpandedZones] = useState<Record<number, boolean>>({ 0: true, 1: true });

    const derived = deriveManufacturing(manufacturingSpec);
    const outerRadius = manufacturingSpec.physical_size_mm / 2;
    const maxEcc = outerRadius / 2;

    function handleSpecChange(key: keyof ManufacturingSpec, value: number) {
        setManufacturingSpec({ ...manufacturingSpec, [key]: value });
    }

    function handleZoneChange(zoneIndex: number, key: keyof PatternZone, value: unknown) {
        const updatedZones = config.zones.map((z, i) =>
            i === zoneIndex ? { ...z, [key]: value } : z
        );
        setConfig({ ...config, zones: updatedZones });
    }

    function handleEngineChange(zoneIndex: number, key: keyof RoseEngineParams, value: unknown) {
        const updatedZones = config.zones.map((z, i) =>
            i === zoneIndex ? { ...z, engine: { ...z.engine, [key]: value } } : z
        );
        setConfig({ ...config, zones: updatedZones });
    }

    function addZone() {
        if (config.zones.length >= 4) return;
        const lastZone = config.zones[config.zones.length - 1];
        const newZone: PatternZone = {
            inner_radius: 0,
            outer_radius: lastZone ? Math.max(lastZone.inner_radius, 1) : outerRadius / 2,
            engine: {
                fixed_radius: outerRadius * 0.4,
                rolling_radius: outerRadius * 0.15,
                cam_amplitude: outerRadius * 0.1,
                phase_shift: 0,
                is_epitrochoid: false,
                rotations: 1,
                radial_step: 0,
            },
            cut_count: 24,
            cut_angle_offset: 15,
            color: ZONE_COLORS[config.zones.length % ZONE_COLORS.length].value,
            label: `Zone ${config.zones.length + 1}`,
        };
        setConfig({ ...config, zones: [...config.zones, newZone] });
        setExpandedZones((prev) => ({ ...prev, [config.zones.length]: true }));
    }

    function removeZone(zoneIndex: number) {
        if (config.zones.length <= 1) return;
        setConfig({ ...config, zones: config.zones.filter((_, i) => i !== zoneIndex) });
    }

    function toggleZone(zoneIndex: number) {
        setExpandedZones((prev) => ({ ...prev, [zoneIndex]: !prev[zoneIndex] }));
    }

    return (
        <aside className="w-80 h-full bg-zinc-950/80 backdrop-blur-xl border-l border-zinc-800/50 flex flex-col overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-zinc-800/50 shrink-0">
                <h2 className="text-xs uppercase tracking-widest text-amber-500 font-semibold">
                    Rose Engine Controls
                </h2>
            </div>

            {/* Scrollable body */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-5">

                {/* History */}
                <div className="flex gap-2">
                    {[
                        { label: "Undo", action: onUndo, disabled: !canUndo },
                        { label: "Redo", action: onRedo, disabled: !canRedo },
                        { label: "Reset", action: onReset, disabled: false },
                    ].map(({ label, action, disabled }) => (
                        <button key={label} onClick={action} disabled={disabled}
                            className="flex-1 text-xs py-1.5 rounded border border-zinc-700 text-zinc-400 disabled:opacity-30 hover:bg-zinc-800 transition">
                            {label}
                        </button>
                    ))}
                </div>

                {/* Presets */}
                <section>
                    <SectionLabel>Presets</SectionLabel>
                    <PresetGallery onSelect={(preset) => setConfig(preset.config)} />
                </section>

                {/* Manufacturing Specs */}
                <section>
                    <SectionLabel>Manufacturing Specs</SectionLabel>
                    <div className="space-y-2">
                        <SliderInput label="Diameter (mm)"
                            value={manufacturingSpec.physical_size_mm}
                            min={10} max={100} step={1}
                            onChange={(v) => handleSpecChange("physical_size_mm", v)} />
                        <SliderInput label="Bore Diameter (mm)"
                            value={manufacturingSpec.bore_size_mm}
                            min={0} max={manufacturingSpec.physical_size_mm * 0.4} step={0.5}
                            onChange={(v) => handleSpecChange("bore_size_mm", v)} />
                        <SliderInput label="Thickness (mm)"
                            value={manufacturingSpec.plate_thickness_mm}
                            min={0.3} max={3.0} step={0.1}
                            onChange={(v) => handleSpecChange("plate_thickness_mm", v)} />
                        <SliderInput label="Cut Depth (mm)"
                            value={manufacturingSpec.cut_depth_mm}
                            min={0.05} max={0.45} step={0.05}
                            onChange={(v) => handleSpecChange("cut_depth_mm", v)} />
                        <SliderInput label="V-Tool Angle (°)"
                            value={manufacturingSpec.tool_angle_deg}
                            min={30} max={90} step={5}
                            onChange={(v) => handleSpecChange("tool_angle_deg", v)} />
                        <SliderInput label="Eccentricity X (mm)"
                            value={manufacturingSpec.eccentricity_x_mm}
                            min={-maxEcc} max={maxEcc} step={0.5}
                            onChange={(v) => handleSpecChange("eccentricity_x_mm", v)} />
                        <SliderInput label="Eccentricity Y (mm)"
                            value={manufacturingSpec.eccentricity_y_mm}
                            min={-maxEcc} max={maxEcc} step={0.5}
                            onChange={(v) => handleSpecChange("eccentricity_y_mm", v)} />

                        <div className="pt-2 border-t border-zinc-800/60 text-[10px] text-zinc-500 space-y-0.5">
                            <div>Groove width: <span className="text-zinc-300 font-mono">{derived.groove_width_mm.toFixed(3)} mm</span></div>
                            <div>Spindle offset: <span className="text-zinc-300 font-mono">
                                ({manufacturingSpec.eccentricity_x_mm.toFixed(1)}, {manufacturingSpec.eccentricity_y_mm.toFixed(1)}) mm
                            </span></div>
                        </div>
                    </div>
                </section>

                {/* Zone Panel */}
                <section>
                    <div className="flex items-center justify-between mb-2">
                        <SectionLabel className="mb-0">Pattern Zones</SectionLabel>
                        <button onClick={addZone} disabled={config.zones.length >= 4}
                            className="text-[10px] px-2 py-1 rounded border border-zinc-700 text-amber-500 hover:bg-amber-500/10 disabled:opacity-30 transition">
                            + Add Zone
                        </button>
                    </div>

                    <div className="space-y-3">
                        {config.zones.map((zone, zoneIndex) => (
                            <div key={zoneIndex}
                                className="rounded-lg border border-zinc-800 bg-zinc-900/50 overflow-hidden">

                                {/* Zone header row */}
                                <div className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-zinc-800/40 transition"
                                    onClick={() => toggleZone(zoneIndex)}>
                                    <div className="w-2.5 h-2.5 rounded-full shrink-0"
                                        style={{ backgroundColor: zone.color }} />
                                    <span className="flex-1 text-xs font-medium text-zinc-300 truncate">
                                        {zone.label}
                                    </span>
                                    <span className="text-[10px] text-zinc-500 font-mono shrink-0">
                                        {zone.inner_radius.toFixed(1)}–{zone.outer_radius.toFixed(1)} mm
                                    </span>
                                    {config.zones.length > 1 && (
                                        <button
                                            onClick={(e) => { e.stopPropagation(); removeZone(zoneIndex); }}
                                            className="text-zinc-600 hover:text-red-400 text-xs ml-1 transition shrink-0">
                                            ✕
                                        </button>
                                    )}
                                    <span className="text-zinc-600 text-[10px] shrink-0">
                                        {expandedZones[zoneIndex] ? "▲" : "▼"}
                                    </span>
                                </div>

                                {expandedZones[zoneIndex] && (
                                    <div className="px-3 pb-3 space-y-2 border-t border-zinc-800/60">

                                        {/* Label + color swatches */}
                                        <div className="flex gap-2 mt-2">
                                            <input type="text" value={zone.label}
                                                onChange={(e) => handleZoneChange(zoneIndex, "label", e.target.value)}
                                                className="flex-1 text-xs bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-amber-500/50"
                                                placeholder="Zone label" />
                                            <div className="flex gap-1 items-center">
                                                {ZONE_COLORS.map((c) => (
                                                    <button key={c.value} onClick={() => handleZoneChange(zoneIndex, "color", c.value)}
                                                        title={c.label}
                                                        className="w-5 h-5 rounded-full border-2 transition"
                                                        style={{ backgroundColor: c.value, borderColor: zone.color === c.value ? "white" : "transparent" }} />
                                                ))}
                                            </div>
                                        </div>

                                        {/* Zone boundaries */}
                                        <SliderInput label="Inner Radius (mm)"
                                            value={zone.inner_radius}
                                            min={0} max={Math.max(zone.outer_radius - 0.5, 0)} step={0.5}
                                            onChange={(v) => handleZoneChange(zoneIndex, "inner_radius", v)} />
                                        <SliderInput label="Outer Radius (mm)"
                                            value={zone.outer_radius}
                                            min={zone.inner_radius + 0.5} max={outerRadius} step={0.5}
                                            onChange={(v) => handleZoneChange(zoneIndex, "outer_radius", v)} />

                                        {/* Cut repetition */}
                                        <SliderInput label="Cuts"
                                            value={zone.cut_count}
                                            min={1} max={96} step={1}
                                            onChange={(v) => handleZoneChange(zoneIndex, "cut_count", v)} />
                                        <SliderInput label="Angle Offset (°)"
                                            value={zone.cut_angle_offset}
                                            min={0} max={360} step={0.5}
                                            onChange={(v) => handleZoneChange(zoneIndex, "cut_angle_offset", v)} />

                                        {/* Kinematics */}
                                        <div className="text-[9px] uppercase tracking-wider text-zinc-600 pt-1">
                                            Kinematics
                                        </div>

                                        <div className="flex rounded overflow-hidden border border-zinc-700 text-xs">
                                            <button onClick={() => handleEngineChange(zoneIndex, "is_epitrochoid", false)}
                                                className={`flex-1 py-1 transition ${!zone.engine.is_epitrochoid ? "bg-amber-500/20 text-amber-400" : "text-zinc-500 hover:bg-zinc-800"}`}>
                                                Hypo
                                            </button>
                                            <button onClick={() => handleEngineChange(zoneIndex, "is_epitrochoid", true)}
                                                className={`flex-1 py-1 transition ${zone.engine.is_epitrochoid ? "bg-amber-500/20 text-amber-400" : "text-zinc-500 hover:bg-zinc-800"}`}>
                                                Epi
                                            </button>
                                        </div>

                                        <SliderInput label="Fixed Radius (mm)"
                                            value={zone.engine.fixed_radius}
                                            min={0.5} max={outerRadius} step={0.1}
                                            onChange={(v) => handleEngineChange(zoneIndex, "fixed_radius", v)} />
                                        <SliderInput label="Rolling Radius (mm)"
                                            value={zone.engine.rolling_radius}
                                            min={0.1} max={outerRadius / 2} step={0.1}
                                            onChange={(v) => handleEngineChange(zoneIndex, "rolling_radius", v)} />
                                        <SliderInput label="Cam Amplitude (mm)"
                                            value={zone.engine.cam_amplitude}
                                            min={0} max={outerRadius / 2} step={0.1}
                                            onChange={(v) => handleEngineChange(zoneIndex, "cam_amplitude", v)} />
                                        <SliderInput label="Phase Shift (°)"
                                            value={zone.engine.phase_shift}
                                            min={0} max={360} step={1}
                                            onChange={(v) => handleEngineChange(zoneIndex, "phase_shift", v)} />
                                        <SliderInput label="Curve Rotations"
                                            value={zone.engine.rotations}
                                            min={0.25} max={10} step={0.25}
                                            onChange={(v) => handleEngineChange(zoneIndex, "rotations", v)} />
                                        <SliderInput label="Radial Step (mm)"
                                            value={zone.engine.radial_step}
                                            min={0} max={1} step={0.01}
                                            onChange={(v) => handleEngineChange(zoneIndex, "radial_step", v)} />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </section>
            </div>

            {/* Generate button */}
            <div className="px-4 py-3 border-t border-zinc-800/50 shrink-0">
                <button onClick={onGenerate} disabled={isGenerating}
                    className="w-full py-2.5 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-400 text-sm font-medium tracking-wide hover:bg-amber-500/30 disabled:opacity-50 transition">
                    {isGenerating ? "Generating…" : "Generate Guilloché"}
                </button>
            </div>
        </aside>
    );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
    return (
        <div className={`text-[10px] uppercase tracking-widest text-amber-500/80 font-semibold mb-2 ${className}`}>
            {children}
        </div>
    );
}

function SliderInput({
    label, value, min, max, step, onChange,
}: {
    label: string; value: number; min: number; max: number; step: number;
    onChange: (v: number) => void;
}) {
    return (
        <div className="space-y-0.5">
            <div className="flex justify-between text-[10px]">
                <span className="text-zinc-400">{label}</span>
                <span className="text-zinc-300 font-mono">{value.toFixed(step < 1 ? 2 : 0)}</span>
            </div>
            <input type="range" min={min} max={max} step={step} value={value}
                onChange={(e) => onChange(parseFloat(e.target.value))}
                className="w-full h-1 appearance-none bg-zinc-700 rounded-full cursor-pointer accent-amber-500" />
        </div>
    );
}
