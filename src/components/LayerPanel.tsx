import { useState } from "react";
import { Plus, Trash2, Eye, EyeOff, GripVertical } from "lucide-react";

export interface PatternLayer {
  id: string;
  name: string;
  visible: boolean;
  opacity: number;
  blendMode: "Add" | "Multiply" | "Subtract";
  patternType: string;
  params: any;
}

interface LayerPanelProps {
  layers: PatternLayer[];
  onLayersChange: (layers: PatternLayer[]) => void;
  onAddLayer: () => void;
  activeLayerId?: string;
  onSelectLayer: (id: string) => void;
}

export function LayerPanel({
  layers,
  onLayersChange,
  onAddLayer,
  activeLayerId,
  onSelectLayer,
}: LayerPanelProps) {
  const handleToggleVisibility = (id: string) => {
    onLayersChange(
      layers.map((layer) =>
        layer.id === id ? { ...layer, visible: !layer.visible } : layer
      )
    );
  };

  const handleDeleteLayer = (id: string) => {
    if (layers.length <= 1) return; // Keep at least one layer
    onLayersChange(layers.filter((layer) => layer.id !== id));
  };

  const handleOpacityChange = (id: string, opacity: number) => {
    onLayersChange(
      layers.map((layer) => (layer.id === id ? { ...layer, opacity } : layer))
    );
  };

  const handleBlendModeChange = (
    id: string,
    blendMode: "Add" | "Multiply" | "Subtract"
  ) => {
    onLayersChange(
      layers.map((layer) => (layer.id === id ? { ...layer, blendMode } : layer))
    );
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs uppercase tracking-widest text-zinc-500 font-semibold">
          Layers
        </h3>
        <button
          onClick={onAddLayer}
          className="flex items-center gap-1 px-2 py-1 bg-zinc-800 hover:bg-zinc-700 rounded text-xs text-zinc-300 transition-all"
        >
          <Plus className="w-3 h-3" />
          Add
        </button>
      </div>

      <div className="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
        {layers.map((layer) => (
          <LayerItem
            key={layer.id}
            layer={layer}
            isActive={layer.id === activeLayerId}
            onSelect={() => onSelectLayer(layer.id)}
            onToggleVisibility={() => handleToggleVisibility(layer.id)}
            onDelete={() => handleDeleteLayer(layer.id)}
            onOpacityChange={(opacity) => handleOpacityChange(layer.id, opacity)}
            onBlendModeChange={(mode) => handleBlendModeChange(layer.id, mode)}
            canDelete={layers.length > 1}
          />
        ))}
      </div>
    </div>
  );
}

function LayerItem({
  layer,
  isActive,
  onSelect,
  onToggleVisibility,
  onDelete,
  onOpacityChange,
  onBlendModeChange,
  canDelete,
}: {
  layer: PatternLayer;
  isActive: boolean;
  onSelect: () => void;
  onToggleVisibility: () => void;
  onDelete: () => void;
  onOpacityChange: (opacity: number) => void;
  onBlendModeChange: (mode: "Add" | "Multiply" | "Subtract") => void;
  canDelete: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`
        bg-zinc-900/50 rounded-lg border transition-all
        ${
          isActive
            ? "border-amber-500/50 bg-amber-500/5"
            : "border-zinc-800/50 hover:border-zinc-700"
        }
      `}
    >
      {/* Layer header */}
      <div
        className="flex items-center gap-2 p-2 cursor-pointer"
        onClick={onSelect}
      >
        <GripVertical className="w-3 h-3 text-zinc-600" />

        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleVisibility();
          }}
          className="p-1 hover:bg-zinc-800 rounded transition-all"
        >
          {layer.visible ? (
            <Eye className="w-3 h-3 text-zinc-400" />
          ) : (
            <EyeOff className="w-3 h-3 text-zinc-600" />
          )}
        </button>

        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-zinc-300 truncate">
            {layer.name}
          </div>
          <div className="text-[10px] text-zinc-600">
            {layer.blendMode} • {Math.round(layer.opacity * 100)}%
          </div>
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="text-xs text-zinc-500 hover:text-zinc-300 transition-all"
        >
          {expanded ? "−" : "+"}
        </button>

        {canDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-1 hover:bg-red-500/20 rounded transition-all"
          >
            <Trash2 className="w-3 h-3 text-zinc-600 hover:text-red-500" />
          </button>
        )}
      </div>

      {/* Layer controls (expanded) */}
      {expanded && (
        <div className="px-2 pb-2 space-y-2 border-t border-zinc-800/50 pt-2">
          {/* Opacity slider */}
          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <label className="text-[10px] uppercase tracking-wider text-zinc-500">
                Opacity
              </label>
              <span className="text-[10px] text-zinc-400 font-mono">
                {Math.round(layer.opacity * 100)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={layer.opacity}
              onChange={(e) => onOpacityChange(parseFloat(e.target.value))}
              className="w-full h-1 bg-zinc-800 rounded-full appearance-none outline-none accent-amber-500"
            />
          </div>

          {/* Blend mode selector */}
          <div className="space-y-1">
            <label className="text-[10px] uppercase tracking-wider text-zinc-500">
              Blend Mode
            </label>
            <div className="flex gap-1">
              {(["Add", "Multiply", "Subtract"] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => onBlendModeChange(mode)}
                  className={`
                    flex-1 px-2 py-1 text-[10px] rounded transition-all
                    ${
                      layer.blendMode === mode
                        ? "bg-amber-500/20 text-amber-500"
                        : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                    }
                  `}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
