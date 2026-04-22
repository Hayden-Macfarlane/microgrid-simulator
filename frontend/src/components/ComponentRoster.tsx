"use client";

import { SourceData, LoadData } from "@/types/grid";
import { api } from "@/lib/api";

interface ComponentRosterProps {
  sources: SourceData[];
  loads: LoadData[];
  onRefresh: () => void;
}

/* ------------------------------------------------------------------ */
/* Source row                                                           */
/* ------------------------------------------------------------------ */
function SourceRow({ s, onRefresh }: { s: SourceData; onRefresh: () => void }) {
  const pct = s.max_output_kw > 0 ? (s.current_output_kw / s.max_output_kw) * 100 : 0;
  const typeIcon: Record<string, string> = {
    SolarPanel: "☀️",
    WindTurbine: "💨",
    RTG: "⚛️",
  };

  const handleToggle = async () => {
    await api.toggleSource(s.id);
    onRefresh();
  };

  return (
    <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-bg-card-hover transition-colors animate-slide-in">
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

      {/* Toggle */}
      <button
        onClick={handleToggle}
        className={`px-2 py-1 flex-shrink-0 text-[10px] uppercase font-bold rounded ${
          s.is_manually_disabled ? "bg-accent-blue/20 text-accent-cyan" : "bg-bg-dark text-text-muted border border-border-subtle"
        } hover:bg-accent-blue/30 transition-colors`}
      >
        {s.is_manually_disabled ? "Resume" : "Halt"}
      </button>

      {/* Value */}
      <span className="font-mono text-sm text-accent-cyan whitespace-nowrap min-w-[3.5rem] text-right">
        {s.current_output_kw.toFixed(1)}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Load row                                                             */
/* ------------------------------------------------------------------ */
function LoadRow({ l, onRefresh }: { l: LoadData; onRefresh: () => void }) {
  const typeIcon: Record<string, string> = {
    LifeSupport: "❤️",
    Heater: "🔥",
    Lighting: "💡",
  };

  const pct = l.max_draw_kw > 0 ? (l.current_draw_kw / l.max_draw_kw) * 100 : 0;
  
  const isThrottled = l.is_active && !l.is_manually_disabled && l.current_draw_kw > 0 && l.current_draw_kw < l.max_draw_kw;
  const isShed = l.is_active && !l.is_manually_disabled && l.current_draw_kw === 0;

  const handleToggle = async () => {
    await api.toggleLoad(l.id);
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
        {l.current_draw_kw.toFixed(1)}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main Component Roster                                                */
/* ------------------------------------------------------------------ */
export default function ComponentRoster({ sources, loads, onRefresh }: ComponentRosterProps) {
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
            sources.map((s) => <SourceRow key={s.id} s={s} onRefresh={onRefresh} />)
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
            loads.map((l) => <LoadRow key={l.id} l={l} onRefresh={onRefresh} />)
          )}
        </div>
      </div>
    </section>
  );
}
