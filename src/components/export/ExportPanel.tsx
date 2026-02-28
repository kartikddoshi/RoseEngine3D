import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { save } from "@tauri-apps/plugin-dialog";
import { Download, FileJson, FileCode } from "lucide-react";
import type { CutPath, ZonedPatternConfig } from "../../types/generator";

interface ExportPanelProps {
  paths: CutPath[];
  config: ZonedPatternConfig;
}

export function ExportPanel({ paths, config }: ExportPanelProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExportSVG = async () => {
    try {
      setIsExporting(true);
      const filePath = await save({
        filters: [{ name: "SVG", extensions: ["svg"] }],
        defaultPath: "guilloche-pattern.svg",
      });

      if (filePath) {
        await invoke("export_pattern_svg", {
          paths,
          filePath,
          width: 200,
          height: 200,
        });
        console.log("SVG exported successfully");
      }
    } catch (e) {
      console.error("Failed to export SVG:", e);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportConfig = async () => {
    try {
      setIsExporting(true);
      const filePath = await save({
        filters: [{ name: "JSON", extensions: ["json"] }],
        defaultPath: "guilloche-config.json",
      });

      if (filePath) {
        await invoke("export_pattern_config", {
          config,
          filePath,
        });
        console.log("Config exported successfully");
      }
    } catch (e) {
      console.error("Failed to export config:", e);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportData = async () => {
    try {
      setIsExporting(true);
      const filePath = await save({
        filters: [{ name: "JSON", extensions: ["json"] }],
        defaultPath: "guilloche-data.json",
      });

      if (filePath) {
        await invoke("export_pattern_data", {
          paths,
          filePath,
        });
        console.log("Data exported successfully");
      }
    } catch (e) {
      console.error("Failed to export data:", e);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="absolute bottom-6 right-6 z-10">
      <div className="bg-zinc-950/80 backdrop-blur-xl border border-zinc-800 rounded-xl p-4 shadow-2xl">
        <h3 className="text-xs uppercase tracking-widest text-zinc-500 font-semibold mb-3">
          Export
        </h3>

        <div className="flex flex-col gap-2">
          <button
            onClick={handleExportSVG}
            disabled={isExporting || paths.length === 0}
            className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-300 px-3 py-2 rounded-lg text-sm transition-all group"
          >
            <FileCode className="w-4 h-4 text-amber-500 group-hover:text-amber-400" />
            SVG Pattern
          </button>

          <button
            onClick={handleExportConfig}
            disabled={isExporting}
            className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-300 px-3 py-2 rounded-lg text-sm transition-all group"
          >
            <FileJson className="w-4 h-4 text-blue-500 group-hover:text-blue-400" />
            Config JSON
          </button>

          <button
            onClick={handleExportData}
            disabled={isExporting || paths.length === 0}
            className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-300 px-3 py-2 rounded-lg text-sm transition-all group"
          >
            <Download className="w-4 h-4 text-green-500 group-hover:text-green-400" />
            Data JSON
          </button>
        </div>
      </div>
    </div>
  );
}
