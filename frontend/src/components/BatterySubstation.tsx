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

  const handleToggleGridForming = async (id: string) => {
    await api.toggleGridForming(id);
    onRefresh();
  };

  const handleRepair = async (id: string) => {
    try {
      await api.repairBattery(id);
      onRefresh();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleScrap = async (id: string) => {
    if (!confirm("Are you sure you want to scrap this battery? It will be permanently removed after 50 ticks.")) return;
    try {
      await api.scrapBattery(id);
      onRefresh();
    } catch (err: any) {
      alert(err.message);
    }
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
          const isFrozen = m.temperature < 5.0;
          const isFreezeDamaging = m.temperature < 0.0;
          
          const bgStatus = m.is_destroyed
            ? "border-accent-red grayscale opacity-75"
            : !m.is_online
            ? "border-bg-dark bg-bg-card-hover opacity-75"
            : isThrottleActive
            ? "border-accent-amber/50 bg-bg-card-hover"
            : "border-border-subtle bg-bg-card";

          // Capacity calculation
          const totalMax = m.max_capacity_kwh;
          const effectiveMax = m.effective_max_capacity;
          const current = m.current_charge_kwh;
          
          const chargePct = totalMax > 0 ? (current / totalMax) * 100 : 0;
          const gapPct = totalMax > 0 ? ((totalMax - effectiveMax) / totalMax) * 100 : 0;
          const usableEmptyPct = totalMax > 0 ? ((effectiveMax - current) / totalMax) * 100 : 0;

          const repairPct = m.is_repairing ? Math.max(0, 100 - (m.energy_debt / ((100 - m.health_percentage) * 5.0)) * 100) : 0;
          const scrapPct = m.is_scrapping ? (m.scrap_progress / 50) * 100 : 0;

          // Tooltip logic
          let healthTooltip = "Battery Health";
          if (isFreezeDamaging) healthTooltip = "❄️ PHYSICAL DAMAGE: FREEZING";
          else if (isHot) healthTooltip = "🔥 CATASTROPHIC FAILURE: THERMAL RUNAWAY";
          else if (current < (totalMax * (m.user_soc_min/100)) || current > (totalMax * (m.user_soc_max/100))) {
              healthTooltip = "⚡ CHEMICAL STRAIN: OPERATING OUTSIDE SAFE SOC";
          }

          return (
            <div key={m.id} className={`card p-4 transition-all border ${bgStatus} relative group overflow-hidden`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{m.is_destroyed ? "💀" : "🔋"}</span>
                  <h3 className="text-sm font-semibold truncate max-w-[150px]">{m.name}</h3>
                </div>
                <button
                  disabled={m.is_scrapping}
                  onClick={() => handleToggle(m.id)}
                  className={`px-2 py-1 text-[10px] uppercase font-bold rounded flex-shrink-0 transition-colors ${
                    m.is_online
                      ? "bg-bg-dark text-text-muted border border-border-subtle hover:bg-bg-card-hover"
                      : "bg-accent-red/20 text-accent-red hover:bg-accent-red/30"
                  }`}
                >
                </button>
              </div>

              {/* Grid-Forming Synthetic Inertia Status */}
              {m.is_grid_forming && !m.is_destroyed && m.is_online && (
                  <div className="mb-2 px-2 py-0.5 bg-accent-blue/10 border border-accent-blue/30 rounded flex items-center justify-between">
                      <span className="text-[9px] font-bold uppercase text-accent-blue tracking-tighter">Synthetic Inertia Online</span>
                      <span className="text-[9px] font-mono text-accent-blue">M=+3.5</span>
                  </div>
              )}

              <div className="space-y-3">
                {/* Visual Capacity Bar */}
                {m.is_scrapping ? (
                    <div className="space-y-1">
                        <div className="flex justify-between text-[10px] uppercase font-bold text-accent-amber">
                            <span>Scrapping Module...</span>
                            <span>{m.scrap_progress}/50 Ticks</span>
                        </div>
                        <div className="h-1.5 w-full bg-bg-dark rounded-full overflow-hidden">
                            <div className="h-full bg-accent-amber transition-all duration-300" style={{ width: `${scrapPct}%` }} />
                        </div>
                    </div>
                ) : m.is_repairing ? (
                    <div className="space-y-1">
                        <div className="flex justify-between text-[10px] uppercase font-bold text-accent-green">
                            <span>Repairing...</span>
                            <span>{m.energy_debt.toFixed(1)} kWh Left</span>
                        </div>
                        <div className="h-1.5 w-full bg-bg-dark rounded-full overflow-hidden">
                            <div className="h-full bg-accent-green transition-all duration-300" style={{ width: `${repairPct}%` }} />
                        </div>
                    </div>
                ) : m.is_destroyed ? (
                  <div className="bg-accent-red/10 border border-accent-red/30 rounded p-2 text-center">
                    <span className="text-[10px] text-accent-red font-bold animate-pulse tracking-tighter">
                      SUBSTATION CRITICAL: PERMANENT FAILURE
                    </span>
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between text-[11px] font-mono text-text-muted mb-1">
                      <span className="flex items-center gap-1">
                        {current.toFixed(1)} kWh {isFrozen && <span className="text-accent-blue animate-pulse">❄️</span>}
                      </span>
                      <span>{effectiveMax.toFixed(1)} kWh</span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden bg-bg-dark flex relative">
                      <div
                        className={`h-full transition-all duration-700 ease-out`}
                        style={{
                          width: `${chargePct}%`,
                          background: m.is_online
                            ? "linear-gradient(90deg, #10b981, #34d399)"
                            : "#475569",
                        }}
                      />
                      {/* Usable Empty Space */}
                      <div style={{ width: `${usableEmptyPct}%` }} />
                      {/* Cold Soak Gap (Hatched) */}
                      {gapPct > 0 && (
                        <div
                          className="h-full"
                          style={{
                            width: `${gapPct}%`,
                            background: "repeating-linear-gradient(45deg, #1e293b, #1e293b 5px, #334155 5px, #334155 10px)",
                          }}
                        />
                      )}
                    </div>
                  </div>
                )}

                {/* Grid stats */}
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono border-t border-border-subtle pt-2">
                  <div className="flex justify-between">
                    <span className="text-text-muted/70">Health</span>
                    <span 
                      title={healthTooltip}
                      className={m.health_percentage < 80 ? "text-accent-red font-bold cursor-help" : "text-text-muted cursor-help"}
                    >
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

                {/* Maintenance Actions */}
                <div className="grid grid-cols-1 gap-2 pt-1">
                    {!m.is_repairing && !m.is_destroyed && m.health_percentage < 100 && (
                        <button
                            onClick={() => handleRepair(m.id)}
                            className="bg-accent-green/10 text-accent-green text-[10px] uppercase font-bold py-1.5 rounded hover:bg-accent-green/20 border border-accent-green/30 transition-all"
                        >
                            Start Repair Cycle
                        </button>
                    )}
                    {m.is_destroyed && !m.is_scrapping && (
                        <button
                            onClick={() => handleScrap(m.id)}
                            className="bg-accent-amber/10 text-accent-amber text-[10px] uppercase font-bold py-1.5 rounded hover:bg-accent-amber/20 border border-accent-amber/30 transition-all"
                        >
                            Scrap for Materials
                        </button>
                    )}
                    {!m.is_destroyed && m.is_online && (
                        <button
                            onClick={() => handleToggleGridForming(m.id)}
                            className={`text-[10px] uppercase font-bold py-1.5 rounded border transition-all ${
                                m.is_grid_forming 
                                ? "bg-accent-blue/20 text-accent-blue border-accent-blue/50 hover:bg-accent-blue/30" 
                                : "bg-bg-dark text-text-muted border-border-subtle hover:bg-bg-card-hover"
                            }`}
                        >
                            {m.is_grid_forming ? "Disable Grid-Forming" : "Enable Grid-Forming"}
                        </button>
                    )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
