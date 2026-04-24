"use client";

import { SourceData, LoadData, EnvironmentState } from "@/types/grid";
import { api } from "@/lib/api";

interface ComponentRosterProps {
  sources: SourceData[];
  loads: LoadData[];
  environment?: EnvironmentState;
  onRefresh: () => void;
}

/* ------------------------------------------------------------------ */
/* Source row                                                           */
/* ------------------------------------------------------------------ */
function SourceRow({ s, environment, onRefresh }: { s: SourceData; environment?: EnvironmentState; onRefresh: () => void }) {
  const pct = s.max_output_kw > 0 ? (s.current_output_kw / s.max_output_kw) * 100 : 0;
  const typeIcon: Record<string, string> = {
    SolarPanel: "☀️",
    WindTurbine: "💨",
    RTG: "⚛️",
    KineticFlywheel: "🎡",
  };

  const handleToggle = async () => {
    await api.toggleSource(s.id);
    onRefresh();
  };

  const handleClean = async () => {
    try {
      await api.cleanSolar(s.id);
      onRefresh();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const isSolar = s.type === "SolarPanel";

  return (
    <div className="flex flex-col gap-1 px-3 py-2.5 rounded-lg hover:bg-bg-card-hover transition-colors animate-slide-in">
      <div className="flex items-center gap-3">
        {/* Icon */}
        <span className="text-lg w-7 text-center">{typeIcon[s.type] || "⚡"}</span>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">{s.name}</span>
            {!s.is_operational && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-red/20 text-accent-red uppercase">
                Offline
              </span>
            )}
            {s.is_manually_disabled && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-text-muted/20 text-text-muted uppercase tracking-wider">
                Override
              </span>
            )}
            {s.is_cleaning && (
               <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-green/20 text-accent-green uppercase tracking-wider animate-pulse">
                 Cleaning...
               </span>
            )}
            {environment && s.type === "SolarPanel" && environment.solar_efficiency < 0.1 && s.is_operational && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-bg-dark text-text-muted uppercase tracking-wider border border-border-subtle">
                Night Mode (0%)
              </span>
            )}
            {environment && s.type === "SolarPanel" && environment.current_event === "Dust Storm" && s.is_operational && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-amber/20 text-accent-amber uppercase tracking-wider">
                Dust Storm (x0.1)
              </span>
            )}
            {environment && s.type === "WindTurbine" && environment.current_event === "Dust Storm" && s.is_operational && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-amber/20 text-accent-amber uppercase tracking-wider">
                Dust Storm (x1.5)
              </span>
            )}
            {environment && s.type === "WindTurbine" && environment.current_event === "High Winds" && s.is_operational && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-red/20 text-accent-red uppercase tracking-wider">
                High Winds (x2.0)
              </span>
            )}
          </div>
          {/* Output bar */}
          <div className="mt-1 h-1.5 rounded-full bg-border-subtle overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out"
              style={{
                width: `${Math.min(pct, 100)}%`,
                background: (s.is_operational && !s.is_manually_disabled)
                  ? "linear-gradient(90deg, #22d3ee, #60a5fa)"
                  : "#475569",
              }}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
            {isSolar && s.dust_coverage !== undefined && s.dust_coverage > 0 && !s.is_cleaning && (
                <button
                    onClick={handleClean}
                    title="Clean accumulated dust"
                    className="px-2 py-1 text-[10px] uppercase font-bold rounded bg-accent-green/10 text-accent-green border border-accent-green/30 hover:bg-accent-green/20 transition-all"
                >
                    Clean
                </button>
            )}
            <button
                onClick={handleToggle}
                className={`px-2 py-1 flex-shrink-0 text-[10px] uppercase font-bold rounded ${
                s.is_manually_disabled ? "bg-accent-blue/20 text-accent-cyan" : "bg-bg-dark text-text-muted border border-border-subtle"
                } hover:bg-accent-blue/30 transition-colors`}
            >
                {s.is_manually_disabled ? "Resume" : "Halt"}
            </button>
        </div>

        {/* Value */}
        <span className="font-mono text-sm text-accent-cyan whitespace-nowrap min-w-[3.5rem] text-right">
          {s.current_output_kw.toFixed(1)}
        </span>
      </div>
      
      {/* Dust Coverage Footer for Solar */}
      {isSolar && s.dust_coverage !== undefined && (
          <div className="flex justify-between items-center ml-10 mr-16">
              <span className="text-[9px] uppercase font-mono text-text-muted/60">Surface Contamination</span>
              <div className="flex items-center gap-2 flex-1 mx-3">
                  <div className="h-1 flex-1 bg-bg-dark rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-accent-amber/50" 
                        style={{ width: `${s.dust_coverage}%` }}
                      />
                  </div>
                  <span className={`text-[10px] font-mono ${s.dust_coverage > 50 ? 'text-accent-amber' : 'text-text-muted'}`}>
                      {s.dust_coverage.toFixed(2)}%
                  </span>
              </div>
          </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Load row                                                             */
/* ------------------------------------------------------------------ */
function LoadRow({ l, environment, onRefresh }: { l: LoadData; environment?: EnvironmentState; onRefresh: () => void }) {
  const typeIcon: Record<string, string> = {
    LifeSupport: "❤️",
    Heater: "🔥",
    Lighting: "💡",
    ExternalComms: "📡",
    WaterFiltration: "💧",
    ScienceLab: "🔬",
    RoverBay: "🚜",
    Extractors: "⛏️",
  };

  const pct = l.max_draw_kw > 0 ? (l.current_draw_kw / l.max_draw_kw) * 100 : 0;
  const isVolatile = l.schedule_type === "spiky" || l.variance_percentage > 0.1;
  
  const isThrottled = l.is_active && !l.is_manually_disabled && l.is_grid_throttled;
  const isShed = l.is_active && !l.is_manually_disabled && l.current_draw_kw === 0;

  const handleToggle = async () => {
    await api.toggleLoad(l.id);
    onRefresh();
  };

  const handleTierChange = async (tier: number) => {
    await api.setUFLSTier(l.id, tier);
    onRefresh();
  };

  return (
    <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-card-hover transition-colors animate-slide-in">
      {/* Icon */}
      <span className="text-lg w-7 text-center">{typeIcon[l.type] || "🔌"}</span>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{l.name}</span>
          {l.is_essential && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-red/20 text-accent-red uppercase tracking-wider">
              Essential
            </span>
          )}
          {!l.is_active && l.repair_ticks_remaining === 0 && !l.is_manually_disabled && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-text-muted/20 text-text-muted uppercase">
              Offline
            </span>
          )}
          {isShed && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-border-subtle/50 text-text-muted uppercase">
              Shed
            </span>
          )}
          {isThrottled && (
             <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-amber/20 text-accent-amber uppercase tracking-wider">
               Throttled ({pct.toFixed(0)}%)
             </span>
          )}
          {l.is_manually_disabled && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-red/20 text-accent-red uppercase tracking-wider">
              OFFLINE (MANUAL)
            </span>
          )}
          {environment && l.type === "Heater" && environment.current_event === "Cold Snap" && l.is_active && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-blue/20 text-accent-blue uppercase tracking-wider">
              Cold Snap (x3.0)
            </span>
          )}
          {environment && l.type === "LifeSupport" && environment.current_event === "Cold Snap" && l.is_active && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-blue/20 text-accent-blue uppercase tracking-wider">
              Cold Snap (x3.0)
            </span>
          )}
          {environment && (l.type === "ScienceLab" || l.type === "RoverBay" || l.type === "Extractors") && environment.day_activity_demand < 0.6 && l.is_active && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-bg-dark text-text-muted uppercase tracking-wider border border-border-subtle">
              Night Operations
            </span>
          )}
          {l.ufls_tier > 0 && (
            <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase tracking-wider border ${
              l.ufls_tier === 1 ? 'border-accent-red/40 text-accent-red' : 
              l.ufls_tier === 2 ? 'border-accent-amber/40 text-accent-amber' : 
              'border-text-muted/40 text-text-muted'
            }`}>
              Tier {l.ufls_tier}
            </span>
          )}
          {isVolatile && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-accent-amber/20 text-accent-amber uppercase tracking-wider">
              ⚡ Volatile
            </span>
          )}
        </div>
        {/* Draw indicator */}
        <div className="mt-1 h-1.5 rounded-full bg-border-subtle overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${Math.min(pct, 100)}%`,
              background: l.is_essential
                ? "linear-gradient(90deg, #f87171, #fbbf24)"
                : isThrottled ? "linear-gradient(90deg, #fbbf24, #d97706)" : "linear-gradient(90deg, #a78bfa, #60a5fa)",
            }}
          />
        </div>
      </div>

      {/* Tier Selector */}
      <div className="flex flex-col gap-1 mr-2 min-w-[70px]">
        <span className="text-[8px] uppercase text-text-muted/60 font-bold text-center">UFLS Tier</span>
        <select
          value={l.ufls_tier}
          onChange={(e) => handleTierChange(parseInt(e.target.value))}
          className="bg-bg-dark text-[10px] text-text-muted border border-border-subtle rounded px-1 py-0.5 cursor-pointer hover:border-accent-cyan transition-colors appearance-none text-center"
        >
          <option value={0}>Safe</option>
          <option value={1}>T1</option>
          <option value={2}>T2</option>
          <option value={3}>T3</option>
        </select>
      </div>

      {/* Toggle */}
      <button
        onClick={handleToggle}
        className={`px-2 py-1 flex-shrink-0 text-[10px] uppercase font-bold rounded ${
          l.is_manually_disabled ? "bg-accent-blue/20 text-accent-cyan" : "bg-bg-dark text-text-muted border border-border-subtle"
        } hover:bg-accent-blue/30 transition-colors`}
      >
        {l.is_manually_disabled ? "Resume" : "Halt"}
      </button>

      {/* Value */}
      <span className="font-mono text-sm text-accent-amber whitespace-nowrap min-w-[3.5rem] text-right">
        {l.current_draw_kw.toFixed(1)} kW
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main Component Roster                                                */
/* ------------------------------------------------------------------ */
export default function ComponentRoster({ sources, loads, environment, onRefresh }: ComponentRosterProps) {
  return (
    <section className="space-y-4 animate-fade-in">
      <h2 className="text-lg font-semibold tracking-wide uppercase text-text-secondary flex items-center gap-3">
        <span className="inline-block h-2.5 w-2.5 rounded-full bg-accent-cyan" />
        Component Roster
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Sources */}
        <div className="card p-4 space-y-1">
          <h3 className="text-[11px] uppercase tracking-widest text-text-muted font-mono mb-2">
            Power Sources ({sources.length})
          </h3>
          {sources.length === 0 ? (
            <p className="text-sm text-text-muted py-4 text-center">No sources connected</p>
          ) : (
            sources.map((s) => <SourceRow key={s.id} s={s} environment={environment} onRefresh={onRefresh} />)
          )}
        </div>

        {/* Loads */}
        <div className="card p-4 space-y-1">
          <h3 className="text-[11px] uppercase tracking-widest text-text-muted font-mono mb-2">
            Power Loads ({loads.length})
          </h3>
          {loads.length === 0 ? (
            <p className="text-sm text-text-muted py-4 text-center">No loads connected</p>
          ) : (
            loads.map((l) => <LoadRow key={l.id} l={l} environment={environment} onRefresh={onRefresh} />)
          )}
        </div>
      </div>
    </section>
  );
}
