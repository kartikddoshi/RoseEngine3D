import { Sparkles } from "lucide-react";
import { presets, type Preset } from "../data/presets";

interface PresetGalleryProps {
  onSelect: (preset: Preset) => void;
}

export function PresetGallery({ onSelect }: PresetGalleryProps) {
  return (
    <div className="grid grid-cols-2 gap-2 max-h-52 overflow-y-auto pr-1">
      {presets.map((preset) => (
        <PresetCard key={preset.id} preset={preset} onSelect={() => onSelect(preset)} />
      ))}
    </div>
  );
}

function PresetCard({ preset, onSelect }: { preset: Preset; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className="group relative bg-zinc-900/50 hover:bg-zinc-800/70 border border-zinc-800/50 hover:border-amber-500/30 rounded-lg p-2.5 text-left transition-all hover:scale-[1.02] active:scale-[0.98]"
    >
      <div className="w-full aspect-square bg-zinc-950 rounded-md mb-1.5 flex items-center justify-center border border-zinc-800">
        <Sparkles className="w-5 h-5 text-zinc-700 group-hover:text-amber-500/50 transition-colors" />
      </div>
      <h4 className="text-[10px] font-semibold text-zinc-300 group-hover:text-amber-500 transition-colors truncate">
        {preset.name}
      </h4>
      <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-amber-500/0 to-amber-500/0 group-hover:from-amber-500/5 group-hover:to-transparent transition-all pointer-events-none" />
    </button>
  );
}
