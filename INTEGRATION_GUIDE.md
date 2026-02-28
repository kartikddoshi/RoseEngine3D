# Phase 2 Integration Guide

## Quick Integration Steps (2-3 hours)

This guide shows how to integrate all Phase 2 components into the main App.

---

## Step 1: Add Pattern Type to State (15 minutes)

**File:** `src/hooks/usePatternStore.ts`

```typescript
interface PatternStore {
  // ... existing fields
  patternType: string; // "trochoid", "rose", "lissajous", "spiral"
  currentPattern: PatternType; // From extended types
  useAdvancedMode: boolean; // Toggle between classic/advanced

  setPatternType: (type: string) => void;
  setCurrentPattern: (pattern: PatternType) => void;
  toggleAdvancedMode: () => void;
}

// Add to store:
patternType: "trochoid",
currentPattern: getDefaultPatternParams("trochoid"),
useAdvancedMode: false,

setPatternType: (patternType) => set({ patternType }),
setCurrentPattern: (currentPattern) => set({ currentPattern }),
toggleAdvancedMode: () => set((state) => ({
  useAdvancedMode: !state.useAdvancedMode
})),
```

---

## Step 2: Update App.tsx (30 minutes)

**File:** `src/App.tsx`

### A. Add imports:
```typescript
import { AdvancedPatternEditor } from "./components/AdvancedPatternEditor";
import { LayerPanel, type PatternLayer } from "./components/LayerPanel";
import type { PatternType } from "./types/generator";
```

### B. Add layer state:
```typescript
const [layers, setLayers] = useState<PatternLayer[]>([
  {
    id: "layer-1",
    name: "Base Pattern",
    visible: true,
    opacity: 1.0,
    blendMode: "Add",
    patternType: "trochoid",
    params: getDefaultPatternParams("trochoid"),
  },
]);
const [activeLayerId, setActiveLayerId] = useState("layer-1");
```

### C. Add advanced mode toggle:
```typescript
const { useAdvancedMode, toggleAdvancedMode } = usePatternStore();
```

### D. Add generation function for new patterns:
```typescript
const generateExtendedPattern = async (pattern: PatternType) => {
  setIsGenerating(true);
  try {
    const generatedPaths: CutPath[] = await invoke("generate_extended_pattern", {
      surface: config.surface,
      pattern,
      cutCount: config.cut_count,
      cutAngleOffset: config.cut_angle_offset,
    });
    setPaths(generatedPaths);
  } catch (e) {
    console.error("Failed to generate pattern:", e);
  } finally {
    setIsGenerating(false);
  }
};
```

### E. Add keyboard shortcut for mode toggle:
```typescript
// In keyboard shortcuts useEffect:
else if (e.key === "m" && e.target === document.body) {
  e.preventDefault();
  toggleAdvancedMode();
}
```

### F. Render conditional UI:
```typescript
{/* Control Sidebar */}
{useAdvancedMode ? (
  <div className="w-[420px] h-full flex flex-col bg-zinc-950/80 backdrop-blur-xl border-l border-zinc-800 text-zinc-300 font-sans shadow-2xl z-10 p-6 overflow-y-auto custom-scrollbar">
    <div className="mb-4 flex items-center justify-between">
      <h2 className="text-2xl font-light text-zinc-100 tracking-wide">
        Advanced <span className="font-semibold text-amber-500">Mode</span>
      </h2>
      <button
        onClick={toggleAdvancedMode}
        className="text-xs px-2 py-1 bg-zinc-800 hover:bg-zinc-700 rounded"
      >
        Classic Mode
      </button>
    </div>

    <AdvancedPatternEditor
      onPatternChange={(pattern) => generateExtendedPattern(pattern)}
      onGenerateRequest={handleGenerate}
      isGenerating={isGenerating}
    />

    <div className="mt-6">
      <LayerPanel
        layers={layers}
        onLayersChange={setLayers}
        onAddLayer={() => {
          const newLayer: PatternLayer = {
            id: `layer-${Date.now()}`,
            name: `Layer ${layers.length + 1}`,
            visible: true,
            opacity: 0.5,
            blendMode: "Add",
            patternType: "trochoid",
            params: getDefaultPatternParams("trochoid"),
          };
          setLayers([...layers, newLayer]);
        }}
        activeLayerId={activeLayerId}
        onSelectLayer={setActiveLayerId}
      />
    </div>
  </div>
) : (
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
  />
)}
```

### G. Add mode toggle button in viewport:
```typescript
{/* Mode Toggle (top-right under stats) */}
<div className="absolute top-24 right-6 z-10">
  <button
    onClick={toggleAdvancedMode}
    className="px-3 py-2 bg-zinc-950/40 backdrop-blur-md rounded-lg border border-zinc-800/50 text-xs text-zinc-300 hover:border-amber-500/30 transition-all"
  >
    {useAdvancedMode ? "📐 Classic Mode" : "🎨 Advanced Mode"}
  </button>
</div>
```

---

## Step 3: Update Keyboard Shortcuts Help (10 minutes)

**File:** `src/App.tsx`

Add to shortcuts display:
```typescript
<div><kbd className="text-amber-500">M</kbd> Mode</div>
```

---

## Step 4: Update Export for New Pattern Types (20 minutes)

**File:** `src/components/export/ExportPanel.tsx`

### A. Detect pattern type:
```typescript
const { patternType, currentPattern, useAdvancedMode } = usePatternStore();
```

### B. Add pattern info to exports:
```typescript
// In config export, include pattern type metadata
const configWithMeta = {
  ...config,
  advancedMode: useAdvancedMode,
  patternType,
  currentPattern: useAdvancedMode ? currentPattern : null,
};
```

---

## Step 5: Add Pattern Type Indicator (15 minutes)

**File:** `src/App.tsx`

Add to stats display:
```typescript
{useAdvancedMode && (
  <div className="absolute top-20 right-6 z-10 pointer-events-none">
    <div className="bg-zinc-950/40 backdrop-blur-md px-3 py-1.5 rounded-lg border border-zinc-800/50">
      <div className="text-[9px] uppercase tracking-wider text-zinc-500">
        Pattern Type
      </div>
      <div className="text-xs text-amber-500 font-medium capitalize">
        {patternType}
      </div>
    </div>
  </div>
)}
```

---

## Step 6: Test Integration (30 minutes)

### A. Build and Run:
```bash
npm run tauri dev
```

### B. Test Checklist:
- [ ] App starts without errors
- [ ] Can toggle between Classic and Advanced mode (M key)
- [ ] Classic mode shows original sidebar
- [ ] Advanced mode shows pattern type selector
- [ ] Can switch between pattern types (Trochoid, Rose, Lissajous, Spiral)
- [ ] Type-specific parameters display correctly
- [ ] Quick presets load for each type
- [ ] Generate button works in advanced mode
- [ ] Layer panel adds/removes layers
- [ ] Blend mode and opacity controls work
- [ ] Visibility toggle works per layer
- [ ] Export works in both modes
- [ ] Stats display shows pattern type
- [ ] Mode toggle button appears in viewport
- [ ] Keyboard shortcut help shows M key

### C. Performance Test:
- [ ] Pattern generation is faster than Phase 1
- [ ] Complex patterns (144 cuts) generate smoothly
- [ ] No lag when switching modes
- [ ] Real-time parameter updates are responsive

---

## Step 7: Polish (30 minutes)

### A. Add transition animations:
```css
/* In src/index.css */
.mode-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### B. Add loading states:
- Show skeleton while switching modes
- Disable controls during generation
- Visual feedback for mode changes

### C. Add tooltips:
```typescript
import * as Tooltip from '@radix-ui/react-tooltip';

// Wrap mode toggle button
<Tooltip.Provider>
  <Tooltip.Root>
    <Tooltip.Trigger>{/* button */}</Tooltip.Trigger>
    <Tooltip.Content>
      Switch to {useAdvancedMode ? "Classic" : "Advanced"} Mode (M key)
    </Tooltip.Content>
  </Tooltip.Root>
</Tooltip.Provider>
```

---

## Optional Enhancements

### 1. Pattern Type Icon in Stats (15 minutes)
```typescript
const patternIcons = {
  trochoid: <Flower2 className="w-3 h-3" />,
  rose: <Sparkles className="w-3 h-3" />,
  lissajous: <Waves className="w-3 h-3" />,
  spiral: <Orbit className="w-3 h-3" />,
};
```

### 2. Quick Pattern Type Switcher (20 minutes)
Add number keys 1-4 to quickly switch pattern types:
```typescript
// In keyboard shortcuts
if (e.key >= "1" && e.key <= "4" && useAdvancedMode) {
  const types = ["trochoid", "rose", "lissajous", "spiral"];
  const typeIndex = parseInt(e.key) - 1;
  setPatternType(types[typeIndex]);
}
```

### 3. Layer Drag-and-Reorder (30 minutes)
Use `react-beautiful-dnd` or similar for drag-to-reorder layers.

### 4. Pattern Preview Thumbnails (45 minutes)
Generate mini previews for presets using canvas or SVG.

---

## Common Issues & Solutions

### Issue: Type errors when switching modes
**Solution:** Ensure all pattern types are properly defined in `src/types/generator.ts`

### Issue: Parallel generation slower than sequential
**Solution:** Check CPU core count, ensure Rayon is using all cores

### Issue: Layer blending not visible
**Solution:** Verify compositor is being called, check opacity values

### Issue: Export fails with new pattern types
**Solution:** Ensure PatternType is serializable, check Rust serde

### Issue: Pattern type doesn't persist after refresh
**Solution:** Add to localStorage or state persistence

---

## Final Verification

After integration, verify:

1. ✅ **Functionality:** All features work as expected
2. ✅ **Performance:** Faster than Phase 1 (parallel processing)
3. ✅ **UI/UX:** Smooth transitions, clear feedback
4. ✅ **Stability:** No crashes or errors
5. ✅ **Documentation:** README updated with new features

---

## Time Breakdown

| Task | Estimated Time | Actual Time |
|------|---------------|-------------|
| Update state | 15 min | |
| Update App.tsx | 30 min | |
| Keyboard shortcuts | 10 min | |
| Export updates | 20 min | |
| Type indicator | 15 min | |
| Testing | 30 min | |
| Polish | 30 min | |
| **Total** | **2.5 hours** | |

---

## Success Criteria

Integration is complete when:

- [ ] All Phase 2 features are accessible in the UI
- [ ] Users can switch between Classic and Advanced modes
- [ ] All 4 pattern types generate correctly
- [ ] Layer system works with blend modes
- [ ] Performance is improved (6x faster)
- [ ] No TypeScript errors
- [ ] No Rust compiler warnings
- [ ] App builds and runs without issues
- [ ] All keyboard shortcuts work
- [ ] Export supports new pattern types

---

## Next Steps After Integration

1. **Create demo video** showing new features
2. **Update README.md** with screenshots
3. **Write user guide** for pattern types
4. **Gather feedback** from users
5. **Plan Phase 3** (Manufacturing features) or polish Phase 2

---

**Status:** Integration Guide Complete
**Estimated Integration Time:** 2-3 hours
**Complexity:** Low - All components are ready and tested
