"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { SimulationSettings } from "@/types/grid";

interface SimulationSettingsPanelProps {
  settings?: SimulationSettings;
  onRefresh: () => void;
}

export default function SimulationSettingsPanel({
  settings,
  onRefresh,
}: SimulationSettingsPanelProps) {
  const [local, setLocal] = useState<SimulationSettings | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);

  // Sync with server state only if not actively editing
  useEffect(() => {
    if (settings && !isEditing) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLocal(settings);
    }
  }, [settings, isEditing]);

  if (!local) return null;

  const handleSave = async () => {
    setLoading(true);
    try {
      await api.updateSettings(local);
      setIsEditing(false);
      onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const update = (key: keyof SimulationSettings, val: number) => {
    setIsEditing(true);
    setLocal((prev) => (prev ? { ...prev, [key]: val } : null));
  };

  return (
    <section className="card p-4 space-y-4 animate-fade-in mb-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-wide uppercase text-text-secondary flex items-center gap-3">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-accent-purple" />
          Simulation Settings
        </h2>
        {isEditing && (
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-1.5 rounded-lg bg-accent-purple/20 text-accent-purple text-xs font-semibold hover:bg-accent-purple/30 border border-accent-purple/30 transition-all disabled:opacity-50"
          >
            {loading ? "Saving…" : "Save Settings"}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <div className="flex flex-col gap-2">
          <label className="text-xs text-text-muted font-mono flex justify-between">
            <span>Failure Chance</span>
            <span className="text-accent-purple">
              {local.base_failure_chance.toFixed(1)}%
            </span>
          </label>
          <input
            type="range"
            min="0"
            max="5"
            step="0.1"
            value={local.base_failure_chance}
            onChange={(e) => update("base_failure_chance", parseFloat(e.target.value))}
            className="accent-accent-purple w-full cursor-pointer"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs text-text-muted font-mono flex justify-between">
            <span>Battery Degradation</span>
            <span className="text-accent-purple">
              {local.battery_degradation_rate.toFixed(1)}%
            </span>
          </label>
          <input
            type="range"
            min="0"
            max="5"
            step="0.1"
            value={local.battery_degradation_rate}
            onChange={(e) => update("battery_degradation_rate", parseFloat(e.target.value))}
            className="accent-accent-purple w-full cursor-pointer"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs text-text-muted font-mono flex justify-between">
            <span>Throttle Threshold</span>
            <span className="text-accent-amber">
              {(local.throttle_threshold * 100).toFixed(1)}%
            </span>
          </label>
          <input
            type="range"
            min="0"
            max="0.8"
            step="0.05"
            value={local.throttle_threshold}
            onChange={(e) => update("throttle_threshold", parseFloat(e.target.value))}
            className="accent-accent-amber w-full cursor-pointer"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs text-text-muted font-mono flex justify-between">
            <span>Shed Threshold</span>
            <span className="text-accent-red">
              {(local.shed_threshold * 100).toFixed(1)}%
            </span>
          </label>
          <input
            type="range"
            min="0"
            max="0.8"
            step="0.05"
            value={local.shed_threshold}
            onChange={(e) => update("shed_threshold", parseFloat(e.target.value))}
            className="accent-accent-red w-full cursor-pointer"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs text-text-muted font-mono flex justify-between">
            <span>Min Repair Ticks</span>
            <span className="text-accent-purple">{local.min_repair_ticks}</span>
          </label>
          <input
            type="range"
            min="1"
            max="30"
            step="1"
            value={local.min_repair_ticks}
            onChange={(e) => update("min_repair_ticks", parseInt(e.target.value))}
            className="accent-accent-purple w-full cursor-pointer"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs text-text-muted font-mono flex justify-between">
            <span>Max Repair Ticks</span>
            <span className="text-accent-purple">{local.max_repair_ticks}</span>
          </label>
          <input
            type="range"
            min="1"
            max="120"
            step="1"
            value={local.max_repair_ticks}
            onChange={(e) => update("max_repair_ticks", parseInt(e.target.value))}
            className="accent-accent-purple w-full cursor-pointer"
          />
        </div>
      </div>
    </section>
  );
}
