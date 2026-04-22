"use client";

import { BatteryGridData, BatteryModuleData } from "@/types/grid";
import { api } from "@/lib/api";

interface BatterySubstationProps {
  batteryGrid: BatteryGridData;
  onRefresh: () => void;
}

export default function BatterySubstation({ batteryGrid, onRefresh }: BatterySubstationProps) {
  if (!batteryGrid || !batteryGrid.modules) return null;

  const handleToggle = async (id: string) => {
    await api.toggleBatteryModule(id);
    onRefresh();
  };

  return (
    <section className="space-y-4 animate-fade-in mt-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-wide uppercase text-text-secondary flex items-center gap-3">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-accent-green" />
          Battery Substation
        </h2>
        {batteryGrid.reserve_unlocked && (
          <span className="text-[10px] uppercase tracking-widest font-bold px-2 py-1 rounded border border-accent-amber/50 text-accent-amber bg-accent-amber/10 animate-pulse">
            Reserve Unlocked
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {batteryGrid.modules.map((m: BatteryModuleData) => {
          const isHot = m.temperature > 40;
          const isThrottleActive = m.temperature > 50;
          const bgStatus = !m.is_online
            ? "border-bg-dark bg-bg-card-hover opacity-75"
            : isThrottleActive
            ? "border-accent-amber/50 bg-bg-card-hover"
            : "border-border-subtle bg-bg-card";

          // Capacity width purely relative to its own baseline vs current max
          const chargePct = m.max_capacity_kwh > 0 ? (m.current_charge_kwh / m.max_capacity_kwh) * 100 : 0;

          return (
            <div key={m.id} className={`card p-4 transition-all border ${bgStatus}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">🔋</span>
                  <h3 className="text-sm font-semibold truncate max-w-[150px]">{m.name}</h3>
                </div>
                <button
                  onClick={() => handleToggle(m.id)}
                  className={`px-2 py-1 text-[10px] uppercase font-bold rounded flex-shrink-0 transition-colors ${
                    m.is_online
                      ? "bg-bg-dark text-text-muted border border-border-subtle hover:bg-bg-card-hover"
                      : "bg-accent-red/20 text-accent-red hover:bg-accent-red/30"
                  }`}
                >
                  {m.is_online ? "Disconnect" : "Connect"}
                </button>
              </div>

              <div className="space-y-3">
                {/* Visual Capacity Bar */}
                <div>
                  <div className="flex justify-between text-[11px] font-mono text-text-muted mb-1">
                    <span>{m.current_charge_kwh.toFixed(1)} kWh</span>
                    <span>{m.max_capacity_kwh.toFixed(1)} kWh</span>
                  </div>
                  <div className="h-2 rounded-full overflow-hidden bg-bg-dark relative">
                    <div
                      className={`h-full transition-all duration-700 ease-out`}
                      style={{
                        width: `${Math.min(chargePct, 100)}%`,
                        background: m.is_online
                          ? "linear-gradient(90deg, #10b981, #34d399)"
                          : "#475569",
                      }}
                    />
                  </div>
                </div>

                {/* Grid stats */}
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono border-t border-border-subtle pt-2">
                  <div className="flex justify-between">
                    <span className="text-text-muted/70">Health</span>
                    <span className={m.health_percentage < 80 ? "text-accent-red font-bold" : "text-text-muted"}>
                      {m.health_percentage.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted/70">Temp</span>
                    <span className={`${isThrottleActive ? "text-accent-red animate-pulse font-bold" : isHot ? "text-accent-amber" : "text-text-muted"}`}>
                      {m.temperature.toFixed(1)}°C
                    </span>
                  </div>
                  <div className="flex justify-between text-text-muted/70">
                    <span>Input</span>
                    <span>{m.max_charge_rate_kw.toFixed(0)} kW</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted/70">Output</span>
                    <span className={isThrottleActive ? "text-accent-amber font-semibold" : "text-text-muted"}>
                      {m.max_discharge_rate_kw.toFixed(0)} kW
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
