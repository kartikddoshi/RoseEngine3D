import { Flower2, Waves, Sparkles, Orbit } from "lucide-react";

interface PatternTypeSelectorProps {
  onSelectType: (type: string) => void;
  currentType: string;
}

const patternTypes = [
  {
    id: "trochoid",
    name: "Trochoid",
    icon: Flower2,
    description: "Classic rose engine patterns",
    color: "amber",
  },
  {
    id: "rose",
    name: "Rose Curve",
    icon: Sparkles,
    description: "Rhodonea flower patterns",
    color: "pink",
  },
  {
    id: "lissajous",
    name: "Lissajous",
    icon: Waves,
    description: "Frequency-based curves",
    color: "blue",
  },
  {
    id: "spiral",
    name: "Spiral",
    icon: Orbit,
    description: "Archimedean & logarithmic",
    color: "purple",
  },
];

export function PatternTypeSelector({
  onSelectType,
  currentType,
}: PatternTypeSelectorProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-xs uppercase tracking-widest text-zinc-500 font-semibold">
        Pattern Type
      </h3>

      <div className="grid grid-cols-2 gap-2">
        {patternTypes.map((type) => {
          const Icon = type.icon;
          const isActive = currentType === type.id;

          return (
            <button
              key={type.id}
              onClick={() => onSelectType(type.id)}
              className={`
                relative group p-3 rounded-lg border transition-all
                ${
                  isActive
                    ? `bg-${type.color}-500/10 border-${type.color}-500/50`
                    : "bg-zinc-900/50 border-zinc-800/50 hover:border-zinc-700"
                }
              `}
            >
              <div className="flex flex-col items-center gap-1.5">
                <Icon
                  className={`w-5 h-5 ${
                    isActive ? `text-${type.color}-500` : "text-zinc-500"
                  }`}
                />
                <div className="text-xs font-medium text-zinc-300">
                  {type.name}
                </div>
                <div className="text-[9px] text-zinc-600 text-center leading-tight">
                  {type.description}
                </div>
              </div>

              {isActive && (
                <div
                  className={`absolute inset-0 rounded-lg bg-gradient-to-br from-${type.color}-500/5 to-transparent pointer-events-none`}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Pattern-specific parameter components

interface TrochoidParamsProps {
  params: any;
  onChange: (params: any) => void;
}

export function TrochoidParams({ params, onChange }: TrochoidParamsProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between bg-zinc-900/50 p-3 rounded-lg border border-zinc-800/50">
        <span className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Type
        </span>
        <div className="flex gap-2">
          <button
            className={`text-xs px-3 py-1.5 rounded-md transition-all ${
              params.is_epitrochoid
                ? "bg-amber-500/20 text-amber-500"
                : "bg-zinc-800 hover:bg-zinc-700"
            }`}
            onClick={() => onChange({ ...params, is_epitrochoid: true })}
          >
            Epi
          </button>
          <button
            className={`text-xs px-3 py-1.5 rounded-md transition-all ${
              !params.is_epitrochoid
                ? "bg-amber-500/20 text-amber-500"
                : "bg-zinc-800 hover:bg-zinc-700"
            }`}
            onClick={() => onChange({ ...params, is_epitrochoid: false })}
          >
            Hypo
          </button>
        </div>
      </div>

      <SliderInput
        label="Fixed Radius (R)"
        value={params.fixed_radius}
        min={10}
        max={100}
        onChange={(v) => onChange({ ...params, fixed_radius: v })}
      />
      <SliderInput
        label="Rolling Radius (r)"
        value={params.rolling_radius}
        min={5}
        max={100}
        onChange={(v) => onChange({ ...params, rolling_radius: v })}
      />
      <SliderInput
        label="Cam Amplitude (d)"
        value={params.cam_amplitude}
        min={0}
        max={100}
        onChange={(v) => onChange({ ...params, cam_amplitude: v })}
      />
      <SliderInput
        label="Phase Shift (deg)"
        value={params.phase_shift}
        min={0}
        max={360}
        onChange={(v) => onChange({ ...params, phase_shift: v })}
      />
      <SliderInput
        label="Rotations"
        value={params.rotations}
        min={1}
        max={50}
        onChange={(v) => onChange({ ...params, rotations: v })}
      />
    </div>
  );
}

export function RoseCurveParams({ params, onChange }: any) {
  return (
    <div className="space-y-4">
      <SliderInput
        label="Petal Count (k)"
        value={params.k || 5}
        min={2}
        max={20}
        step={0.5}
        onChange={(v) => onChange({ ...params, k: v })}
      />
      <SliderInput
        label="Amplitude"
        value={params.amplitude || 50}
        min={10}
        max={100}
        onChange={(v) => onChange({ ...params, amplitude: v })}
      />
      <SliderInput
        label="Rotations"
        value={params.rotations || 10}
        min={1}
        max={50}
        onChange={(v) => onChange({ ...params, rotations: v })}
      />
    </div>
  );
}

export function LissajousParams({ params, onChange }: any) {
  return (
    <div className="space-y-4">
      <SliderInput
        label="X Frequency"
        value={params.freq_x || 3}
        min={1}
        max={10}
        step={0.5}
        onChange={(v) => onChange({ ...params, freq_x: v })}
      />
      <SliderInput
        label="Y Frequency"
        value={params.freq_y || 2}
        min={1}
        max={10}
        step={0.5}
        onChange={(v) => onChange({ ...params, freq_y: v })}
      />
      <SliderInput
        label="Phase Shift (deg)"
        value={params.phase || 0}
        min={0}
        max={360}
        onChange={(v) => onChange({ ...params, phase: v })}
      />
      <SliderInput
        label="X Amplitude"
        value={params.amp_x || 50}
        min={10}
        max={100}
        onChange={(v) => onChange({ ...params, amp_x: v })}
      />
      <SliderInput
        label="Y Amplitude"
        value={params.amp_y || 50}
        min={10}
        max={100}
        onChange={(v) => onChange({ ...params, amp_y: v })}
      />
      <SliderInput
        label="Rotations"
        value={params.rotations || 10}
        min={1}
        max={50}
        onChange={(v) => onChange({ ...params, rotations: v })}
      />
    </div>
  );
}

export function SpiralParams({ params, onChange }: any) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between bg-zinc-900/50 p-3 rounded-lg border border-zinc-800/50">
        <span className="text-xs font-medium uppercase tracking-wider text-zinc-400">
          Type
        </span>
        <div className="flex gap-2">
          <button
            className={`text-xs px-3 py-1.5 rounded-md transition-all ${
              params.spiral_type === "Archimedean"
                ? "bg-purple-500/20 text-purple-500"
                : "bg-zinc-800 hover:bg-zinc-700"
            }`}
            onClick={() => onChange({ ...params, spiral_type: "Archimedean" })}
          >
            Arch
          </button>
          <button
            className={`text-xs px-3 py-1.5 rounded-md transition-all ${
              params.spiral_type === "Logarithmic"
                ? "bg-purple-500/20 text-purple-500"
                : "bg-zinc-800 hover:bg-zinc-700"
            }`}
            onClick={() => onChange({ ...params, spiral_type: "Logarithmic" })}
          >
            Log
          </button>
        </div>
      </div>

      <SliderInput
        label="Starting Radius (a)"
        value={params.a || 5}
        min={1}
        max={20}
        onChange={(v) => onChange({ ...params, a: v })}
      />
      <SliderInput
        label="Growth Factor (b)"
        value={params.b || 2}
        min={0.1}
        max={5}
        step={0.1}
        onChange={(v) => onChange({ ...params, b: v })}
      />
      <SliderInput
        label="Rotations"
        value={params.rotations || 5}
        min={1}
        max={20}
        onChange={(v) => onChange({ ...params, rotations: v })}
      />
    </div>
  );
}

// Slider component
function SliderInput({
  label,
  value,
  min,
  max,
  step = 0.5,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (val: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5 group">
      <div className="flex justify-between items-end">
        <label className="text-xs font-medium text-zinc-400 group-hover:text-amber-500/80 transition-colors uppercase tracking-wider">
          {label}
        </label>
        <span className="text-xs text-zinc-300 font-mono bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800/50">
          {value}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 bg-zinc-800 rounded-full appearance-none outline-none accent-amber-500 hover:h-2 transition-all cursor-ew-resize"
      />
    </div>
  );
}
