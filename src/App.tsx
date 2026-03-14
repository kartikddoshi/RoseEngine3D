import { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { ParameterSidebar } from "./components/ParameterSidebar";
import { PatternCanvas } from "./components/PatternCanvas";
import { ExportPanel } from "./components/export/ExportPanel";
import type { CutPath, ZonedPatternConfig, ManufacturingSpec } from "./types/generator";
import { specToSurface } from "./types/generator";
import { usePatternStore, initialConfig, initialManufacturingSpec } from "./hooks/usePatternStore";
import "./index.css";

function App() {
  const {
    config,
    zonedPaths,
    isGenerating,
    setConfig,
    setZonedPaths,
    setIsGenerating,
    addToHistory,
    undo,
    redo,
    canUndo,
    canRedo,
  } = usePatternStore();

  const [showExport, setShowExport] = useState(true);
  const [manufacturingSpec, setManufacturingSpec] = useState<ManufacturingSpec>(initialManufacturingSpec);

  const generatePattern = useCallback(async (configToGenerate: ZonedPatternConfig) => {
    setIsGenerating(true);
    try {
      const generatedPaths: CutPath[][] = await invoke("generate_zoned_pattern", {
        config: configToGenerate,
      });
      setZonedPaths(generatedPaths);
    } catch (e) {
      console.error("Failed to generate pattern:", e);
      if ((window as any).__TAURI_INTERNALS__) {
        alert(`Error: ${e}`);
      }
    } finally {
      setIsGenerating(false);
    }
  }, [setIsGenerating, setZonedPaths]);

  const handleConfigChange = useCallback((newConfig: ZonedPatternConfig) => {
    setConfig(newConfig);
    addToHistory(newConfig);
  }, [setConfig, addToHistory]);

  const handleGenerate = useCallback(() => {
    generatePattern(config);
  }, [config, generatePattern]);

  /** When the manufacturing spec changes, update the surface geometry and rescale
   *  zone/engine length params proportionally so the pattern shape is preserved. */
  const handleSpecChange = useCallback((newSpec: ManufacturingSpec) => {
    setManufacturingSpec(newSpec);

    const oldOuterRadius = manufacturingSpec.physical_size_mm / 2;
    const newOuterRadius = newSpec.physical_size_mm / 2;
    const ratio = oldOuterRadius > 0 ? newOuterRadius / oldOuterRadius : 1;

    const newSurface = specToSurface(newSpec);

    const rescaledZones = config.zones.map((zone) => ({
      ...zone,
      inner_radius: zone.inner_radius * ratio,
      outer_radius: zone.outer_radius * ratio,
      engine: {
        ...zone.engine,
        // amplitude and radial_step are physical mm values — scale with dial size
        amplitude: zone.engine.amplitude * ratio,
        radial_step: zone.engine.radial_step * ratio,
      },
    }));

    const newConfig: ZonedPatternConfig = {
      ...config,
      surface: newSurface,
      zones: rescaledZones,
    };

    handleConfigChange(newConfig);
  }, [manufacturingSpec, config, handleConfigChange]);

  const handleUndo = useCallback(() => {
    const previousConfig = undo();
    if (previousConfig) generatePattern(previousConfig);
  }, [undo, generatePattern]);

  const handleRedo = useCallback(() => {
    const nextConfig = redo();
    if (nextConfig) generatePattern(nextConfig);
  }, [redo, generatePattern]);

  const handleReset = useCallback(() => {
    setManufacturingSpec(initialManufacturingSpec);
    handleConfigChange(initialConfig);
    generatePattern(initialConfig);
  }, [handleConfigChange, generatePattern]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      } else if ((e.ctrlKey && e.key === "y") || (e.ctrlKey && e.shiftKey && e.key === "z")) {
        e.preventDefault();
        handleRedo();
      } else if (e.key === " " && e.target === document.body) {
        e.preventDefault();
        handleGenerate();
      } else if (e.key === "r" && e.target === document.body) {
        e.preventDefault();
        handleReset();
      } else if (e.key === "e" && e.target === document.body) {
        e.preventDefault();
        setShowExport((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleUndo, handleRedo, handleGenerate, handleReset]);

  // Generate on initial load
  useEffect(() => {
    generatePattern(config);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalPoints = zonedPaths.reduce(
    (sum, zone) => sum + zone.reduce((s, p) => s + p.points.length, 0),
    0
  );
  const totalCuts = zonedPaths.reduce((sum, zone) => sum + zone.length, 0);

  return (
    <main className="w-screen h-screen flex bg-zinc-950 overflow-hidden text-zinc-100 font-sans">
      {/* 3D Visualizer Viewport */}
      <div className="flex-1 relative">
        <PatternCanvas
          zonedPaths={zonedPaths}
          config={config}
        />

        {/* Floating Header */}
        <div className="absolute top-6 left-6 z-10 pointer-events-none">
          <div className="bg-zinc-950/40 backdrop-blur-md px-4 py-2 rounded-full border border-zinc-800/50 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.8)]"></div>
            <span className="text-xs uppercase tracking-widest text-zinc-300 font-medium">
              Rose Engine Simulation Core
            </span>
          </div>
        </div>

        {/* Stats Display */}
        {totalCuts > 0 && (
          <div className="absolute top-6 right-6 z-10 pointer-events-none">
            <div className="bg-zinc-950/40 backdrop-blur-md px-4 py-2 rounded-lg border border-zinc-800/50">
              <div className="text-[10px] uppercase tracking-wider text-zinc-500 mb-1">
                Pattern Stats
              </div>
              <div className="flex gap-4 text-xs text-zinc-300">
                <div>
                  <span className="text-zinc-500">Zones:</span>{" "}
                  <span className="font-mono">{config.zones.length}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Cuts:</span>{" "}
                  <span className="font-mono">{totalCuts}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Points:</span>{" "}
                  <span className="font-mono">{totalPoints.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Export Panel */}
        {showExport && <ExportPanel paths={zonedPaths.flat()} config={config} />}

        {/* Keyboard Shortcuts Help */}
        <div className="absolute bottom-6 left-6 z-10 pointer-events-none">
          <div className="bg-zinc-950/40 backdrop-blur-md px-3 py-2 rounded-lg border border-zinc-800/50">
            <div className="text-[9px] uppercase tracking-wider text-zinc-500 mb-1.5">
              Shortcuts
            </div>
            <div className="space-y-0.5 text-[10px] text-zinc-400 font-mono">
              <div><kbd className="text-amber-500">Space</kbd> Generate</div>
              <div><kbd className="text-amber-500">Ctrl+Z</kbd> Undo</div>
              <div><kbd className="text-amber-500">Ctrl+Y</kbd> Redo</div>
              <div><kbd className="text-amber-500">R</kbd> Reset</div>
              <div><kbd className="text-amber-500">E</kbd> Export</div>
            </div>
          </div>
        </div>
      </div>

      {/* Control Sidebar */}
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
        setManufacturingSpec={handleSpecChange}
      />
    </main>
  );
}

export default App;
