import { create } from 'zustand';
import type { ZonedPatternConfig, CutPath, ManufacturingSpec } from '../types/generator';
import { specToSurface } from '../types/generator';

interface HistoryState {
    config: ZonedPatternConfig;
    timestamp: number;
}

interface PatternStore {
    config: ZonedPatternConfig;
    zonedPaths: CutPath[][];
    isGenerating: boolean;
    history: HistoryState[];
    historyIndex: number;

    setConfig: (config: ZonedPatternConfig) => void;
    setZonedPaths: (paths: CutPath[][]) => void;
    setIsGenerating: (v: boolean) => void;
    addToHistory: (config: ZonedPatternConfig) => void;
    undo: () => ZonedPatternConfig | null;
    redo: () => ZonedPatternConfig | null;
    canUndo: () => boolean;
    canRedo: () => boolean;
}

export const initialManufacturingSpec: ManufacturingSpec = {
    physical_size_mm: 32,
    bore_size_mm: 4,
    plate_thickness_mm: 0.8,
    cut_depth_mm: 0.30,
    tool_angle_deg: 60,
    eccentricity_x_mm: 0,
    eccentricity_y_mm: 0,
};

export const initialConfig: ZonedPatternConfig = {
    surface: specToSurface(initialManufacturingSpec),
    zones: [
        {
            inner_radius: 8,
            outer_radius: 16,
            engine: {
                fixed_radius: 14,
                rolling_radius: 2.4,
                cam_amplitude: 1.6,
                phase_shift: 0,
                is_epitrochoid: false,
                rotations: 1,
                radial_step: 0,
            },
            cut_count: 48,
            cut_angle_offset: 7.5,
            color: "#d4af37",
            label: "Outer Zone",
        },
        {
            inner_radius: 2,
            outer_radius: 8,
            engine: {
                fixed_radius: 6,
                rolling_radius: 2,
                cam_amplitude: 0.8,
                phase_shift: 0,
                is_epitrochoid: true,
                rotations: 2,
                radial_step: 0.05,
            },
            cut_count: 24,
            cut_angle_offset: 15,
            color: "#c0c0c0",
            label: "Inner Zone",
        },
    ],
};

export const usePatternStore = create<PatternStore>((set, get) => ({
    config: initialConfig,
    zonedPaths: [],
    isGenerating: false,
    history: [{ config: initialConfig, timestamp: Date.now() }],
    historyIndex: 0,

    setConfig: (config) => set({ config }),
    setZonedPaths: (paths) => set({ zonedPaths: paths }),
    setIsGenerating: (v) => set({ isGenerating: v }),

    addToHistory: (config) => {
        const { history, historyIndex } = get();
        const newHistory = history.slice(0, historyIndex + 1);
        const updatedHistory = [
            ...newHistory,
            { config, timestamp: Date.now() },
        ].slice(-50);
        set({
            history: updatedHistory,
            historyIndex: updatedHistory.length - 1,
            config,
        });
    },

    undo: () => {
        const { history, historyIndex } = get();
        if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            const config = history[newIndex].config;
            set({ historyIndex: newIndex, config });
            return config;
        }
        return null;
    },

    redo: () => {
        const { history, historyIndex } = get();
        if (historyIndex < history.length - 1) {
            const newIndex = historyIndex + 1;
            const config = history[newIndex].config;
            set({ historyIndex: newIndex, config });
            return config;
        }
        return null;
    },

    canUndo: () => get().historyIndex > 0,
    canRedo: () => get().historyIndex < get().history.length - 1,
}));
