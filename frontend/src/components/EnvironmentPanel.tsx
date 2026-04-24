"use client";

import { EnvironmentState } from "@/types/grid";

interface EnvironmentPanelProps {
  state?: EnvironmentState;
}

export default function EnvironmentPanel({ state }: EnvironmentPanelProps) {
  if (!state) return null;

  // Format time of day
  const hours = Math.floor(state.time_of_day);
  const minutes = Math.floor((state.time_of_day - hours) * 60);
  const timeString = `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}`;

  const isDay = state.time_of_day >= 6 && state.time_of_day < 18;

  let eventIcon = "🌤️";
  let eventColor = "var(--accent-cyan)";
  let bgClass = "bg-bg-card";
  let borderClass = "border-border-subtle";

  if (state.current_event === "Dust Storm") {
    eventIcon = "🌪️";
    eventColor = "var(--accent-amber)";
    bgClass = "bg-accent-amber/10";
    borderClass = "border-accent-amber/30";
  } else if (state.current_event === "Cold Snap") {
    eventIcon = "❄️";
    eventColor = "var(--accent-blue)";
    bgClass = "bg-accent-blue/10";
    borderClass = "border-accent-blue/30";
  } else if (state.current_event === "High Winds") {
    eventIcon = "🌬️";
    eventColor = "var(--accent-red)";
    bgClass = "bg-accent-red/10";
    borderClass = "border-accent-red/30";
  } else {
    eventIcon = isDay ? "☀️" : "🌙";
  }

  return (
    <div className="flex flex-wrap gap-4 items-center">
      {/* Clock Panel */}
      <div className="card px-4 py-3 flex items-center gap-4 min-w-[200px]">
        <div className="text-3xl">{isDay ? "☀️" : "🌙"}</div>
        <div>
          <div className="text-[10px] uppercase font-mono tracking-widest text-text-muted">Local Time</div>
          <div className="text-xl font-bold font-mono tracking-tight text-text-primary">
            {timeString} <span className="text-xs text-text-muted">HRS</span>
          </div>
        </div>
      </div>

      {/* Weather Panel */}
      <div className={`card px-4 py-3 flex items-center gap-4 min-w-[260px] border transition-colors ${bgClass} ${borderClass}`}>
        <div className="text-3xl">{eventIcon}</div>
        <div>
          <div className="text-[10px] uppercase font-mono tracking-widest text-text-muted">Weather Status</div>
          <div className="text-lg font-bold tracking-wide" style={{ color: eventColor }}>
            {state.current_event.toUpperCase()}
          </div>
          <div className="text-[10px] font-mono uppercase tracking-wider flex items-center gap-1" style={{ color: state.density === "Opaque" ? 'var(--accent-amber)' : state.density === "Dense" ? 'var(--accent-amber)' : 'var(--accent-cyan)' }}>
              <span className={state.density === "Opaque" ? "animate-pulse" : ""}>●</span> 
              Density: {state.density.toUpperCase()}
          </div>
          {state.current_event !== "Clear Skies" && (
            <div className="text-[10px] font-mono mt-0.5 text-text-muted">
              Duration est: {state.event_ticks_remaining} ticks
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
