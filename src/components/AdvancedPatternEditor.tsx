import { useState } from "react";
import { Zap } from "lucide-react";
import {
  PatternTypeSelector,
  TrochoidParams,
  RoseCurveParams,
  LissajousParams,
  SpiralParams,
} from "./PatternTypeSelector";
import { getDefaultPatternParams, getPresetsByType } from "../data/extendedPresets";
import type { PatternType } from "../types/generator";

interface AdvancedPatternEditorProps {
  onPatternChange: (pattern: PatternType) => void;
  onGenerateRequest: () => void;
  isGenerating: boolean;
}

export function AdvancedPatternEditor({
  onPatternChange,
  onGenerateRequest,
  isGenerating,
}: AdvancedPatternEditorProps) {
  const [currentType, setCurrentType] = useState<string>("trochoid");
  const [currentPattern, setCurrentPattern] = useState<PatternType>(
    getDefaultPatternParams("trochoid")
  );

  const handleTypeChange = (newType: string) => {
    setCurrentType(newType);
    const defaultPattern = getDefaultPatternParams(newType);
    setCurrentPattern(defaultPattern);
    onPatternChange(defaultPattern);
  };

  const handleParamsChange = (newParams: any) => {
    const updatedPattern = { ...currentPattern, ...newParams };
    setCurrentPattern(updatedPattern as PatternType);
    onPatternChange(updatedPattern as PatternType);
  };

  const handlePresetLoad = (presetPattern: PatternType) => {
    setCurrentPattern(presetPattern);
    onPatternChange(presetPattern);
  };

  // Get presets for current type
  const typePresets = getPresetsByType(currentType);

  return (
    <div className="space-y-6">
      {/* Pattern Type Selector */}
      <PatternTypeSelector
        currentType={currentType}
        onSelectType={handleTypeChange}
      />

      <div className="w-full h-px bg-gradient-to-r from-transparent via-zinc-800 to-transparent"></div>

      {/* Type-specific Presets */}
      {typePresets.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs uppercase tracking-widest text-zinc-500 font-semibold">
            Quick Presets
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {typePresets.slice(0, 4).map((preset) => (
              <button
                key={preset.id}
                onClick={() => handlePresetLoad(preset.pattern)}
                className="p-2 bg-zinc-900/50 hover:bg-zinc-800/70 border border-zinc-800/50 hover:border-amber-500/30 rounded text-left transition-all"
              >
                <div className="text-xs font-medium text-zinc-300 truncate">
                  {preset.name}
                </div>
                <div className="text-[9px] text-zinc-600 truncate">
                  {preset.description}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="w-full h-px bg-gradient-to-r from-transparent via-zinc-800 to-transparent"></div>

      {/* Pattern Parameters */}
      <div>
        <h4 className="text-xs uppercase tracking-widest text-zinc-500 font-semibold mb-4">
          Parameters
        </h4>

        {currentType === "trochoid" && currentPattern.pattern_type === "Trochoid" && (
          <TrochoidParams
            params={currentPattern}
            onChange={handleParamsChange}
          />
        )}

        {currentType === "rose" && currentPattern.pattern_type === "RoseCurve" && (
          <RoseCurveParams
            params={currentPattern}
            onChange={handleParamsChange}
          />
        )}

        {currentType === "lissajous" && currentPattern.pattern_type === "Lissajous" && (
          <LissajousParams
            params={currentPattern}
            onChange={handleParamsChange}
          />
        )}

        {currentType === "spiral" && currentPattern.pattern_type === "Spiral" && (
          <SpiralParams
            params={currentPattern}
            onChange={handleParamsChange}
          />
        )}
      </div>

      {/* Generate Button with Performance Indicator */}
      <div className="pt-4 border-t border-zinc-800">
        <button
          onClick={onGenerateRequest}
          disabled={isGenerating}
          className="w-full group relative flex items-center justify-center gap-2 bg-gradient-to-b from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 active:scale-[0.98] text-zinc-950 font-semibold rounded-xl py-3.5 px-4 transition-all overflow-hidden disabled:opacity-50 disabled:active:scale-100"
        >
          <Zap className="w-4 h-4" />
          {isGenerating ? "Generating..." : "Generate Pattern"}
          <div className="absolute top-0 right-0 px-2 py-0.5 bg-black/20 text-[9px] font-mono rounded-bl">
            ⚡ Fast
          </div>
        </button>
        <div className="mt-2 text-center text-[9px] text-zinc-600">
          Parallel processing enabled for max speed
        </div>
      </div>
    </div>
  );
}
