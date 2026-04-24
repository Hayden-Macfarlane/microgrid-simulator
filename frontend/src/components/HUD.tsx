"use client";

import { GridState } from "@/types/grid";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

/* ------------------------------------------------------------------ */
/* Frequency Meter (Digital stable grid oscillator)                   */
/* ------------------------------------------------------------------ */
function FrequencyMeter({ 
  frequency, 
  inertia 
}: { 
  frequency: number; 
  inertia: number; 
}) {
  const isCritical = (frequency < 59.5 && frequency > 0) || (frequency === 0);
  const isWarning = frequency < 59.8 || frequency > 60.2;
  
  const color = isCritical ? "var(--accent-red)" : isWarning ? "var(--accent-amber)" : "var(--accent-cyan)";
  const statusText = isCritical ? "CRITICAL INSTABILITY" : isWarning ? "FREQUENCY DEVIATION" : "GRID STABLE";

  return (
    <div className={`card p-4 flex flex-col gap-2 min-w-[200px] border-2 transition-all duration-300 ${isCritical ? 'border-accent-red animate-pulse' : 'border-transparent'}`}
         style={{ background: isCritical ? 'rgba(239, 68, 68, 0.05)' : 'rgba(255, 255, 255, 0.02)' }}>
      <div className="flex justify-between items-center">
        <span className="text-[11px] uppercase tracking-widest text-text-muted font-mono">
          Grid Frequency
        </span>
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${isCritical ? 'bg-accent-red/20 border-accent-red text-accent-red' : 'bg-accent-cyan/10 border-accent-cyan/30 text-accent-cyan'}`}>
          {frequency ? frequency.toFixed(3) : '0.000'} Hz
        </span>
      </div>

      <div className="flex items-center gap-4 mt-1">
        <div className="flex-1 flex flex-col items-center">
           <span className="text-3xl font-bold font-mono tracking-tighter" style={{ color, textShadow: isCritical ? `0 0 10px ${color}` : 'none' }}>
             {frequency ? frequency.toFixed(2) : '0.00'}
             <span className="text-sm ml-1 text-text-muted">Hz</span>
           </span>
        </div>
        
        <div className="w-px h-10 bg-border-subtle" />

        <div className="flex-1 flex flex-col justify-center">
           <span className="text-[10px] uppercase text-text-muted font-mono">Inertia</span>
           <span className="text-lg font-bold text-text-primary">{inertia ? inertia.toFixed(1) : '0.0'} <span className="text-[10px] text-text-muted">s</span></span>
        </div>
      </div>

      <div className="mt-1 space-y-1">
        <div className="flex justify-between text-[9px] uppercase font-mono text-text-muted">
           <span>{statusText}</span>
           <span>Nominal: 60.00 Hz</span>
        </div>
        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden relative">
           <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-white/20 z-10" />
           <div 
             className={`h-full transition-all duration-700 ${color === 'var(--accent-cyan)' ? 'bg-accent-cyan' : isWarning ? 'bg-accent-amber' : 'bg-accent-red'}`}
             style={{ 
               width: `${Math.min(100, Math.abs(frequency - 60) * 20)}%`,
               marginLeft: frequency < 60 ? 'auto' : '50%',
               marginRight: frequency < 60 ? '50%' : 'auto'
             }}
           />
        </div>
      </div>
    </div>
  );
}

interface HUDProps {
  state: GridState | null;
  history: { tick: number; gen: number; demand: number; net: number }[];
}

/* ------------------------------------------------------------------ */
/* Battery Gauge (SVG radial ring)                                     */
/* ------------------------------------------------------------------ */
function BatteryGauge({ 
  pct, 
  charge, 
  max, 
  netPower 
}: { 
  pct: number; 
  charge: number; 
  max: number;
  netPower: number;
}) {
  const radius = 72;
  const stroke = 10;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;

  const color =
    pct > 60 ? "var(--accent-green)" : pct > 25 ? "var(--accent-amber)" : "var(--accent-red)";

  let timerText = "Stable";
  if (netPower > 0.05) {
    const hoursRemaining = (max - charge) / netPower;
    timerText = hoursRemaining > 99 ? ">99h to Full" : `${hoursRemaining.toFixed(1)}h to Full`;
  } else if (netPower < -0.05) {
    const hoursRemaining = charge / Math.abs(netPower);
    timerText = hoursRemaining > 99 ? ">99h to Empty" : `${hoursRemaining.toFixed(1)}h to Empty`;
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={160} height={160} className="drop-shadow-lg">
        {/* Track */}
        <circle
          cx={80}
          cy={80}
          r={radius - 8}
          fill="none"
          stroke="var(--border-subtle)"
          strokeWidth={stroke}
        />
        {/* Fill */}
        <circle
          cx={80}
          cy={80}
          r={radius - 8}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="gauge-ring"
          transform="rotate(-90 80 80)"
          style={{ filter: `drop-shadow(0 0 6px ${color})` }}
        />
        {/* Center text */}
        <text x={80} y={72} textAnchor="middle" fill="var(--text-primary)" fontSize={24} fontWeight={700}>
          {pct.toFixed(1)}%
        </text>
        <text x={80} y={92} textAnchor="middle" fill="var(--text-secondary)" fontSize={10}>
          {charge.toFixed(0)} / {max.toFixed(0)} kWh
        </text>
      </svg>
      <div className={`text-[10px] font-mono font-bold uppercase ${netPower < -0.05 ? 'text-accent-red' : netPower > 0.05 ? 'text-accent-green' : 'text-text-muted'}`}>
        {timerText}
      </div>
      <span className="text-[10px] uppercase tracking-widest text-text-muted font-mono">
        Energy Storage
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Stat Card                                                            */
/* ------------------------------------------------------------------ */
function StatCard({
  label,
  value,
  unit,
  accent,
  children,
}: {
  label: string;
  value: string;
  unit: string;
  accent: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="card p-4 flex flex-col gap-1 min-w-[150px] flex-1">
      <span className="text-[11px] uppercase tracking-widest text-text-muted font-mono">
        {label}
      </span>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-bold" style={{ color: accent }}>
          {value}
        </span>
        <span className="text-xs text-text-secondary">{unit}</span>
      </div>
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Custom Recharts tooltip                                              */
/* ------------------------------------------------------------------ */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: any[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card px-3 py-2 text-xs space-y-1" style={{ border: "1px solid var(--border-glow)" }}>
      <p className="font-mono text-text-muted">Tick {label}</p>
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {p.value.toFixed(2)} kW
        </p>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main HUD Component                                                   */
/* ------------------------------------------------------------------ */
export default function HUD({ state, history }: HUDProps) {
  if (!state) {
    return (
      <div className="card p-8 flex items-center justify-center text-text-muted animate-pulse">
        Connecting to grid…
      </div>
    );
  }

  const netColor = state.net_power_kw >= 0 ? "var(--accent-green)" : "var(--accent-red)";
  const netPrefix = state.net_power_kw >= 0 ? "+" : "";
  const isThermalThrottling = state.battery_grid?.modules?.some((m) => m.temperature > 50);
  const isBottleneck = state.net_power_kw < 0 && Math.abs(state.net_power_kw) > state.battery_grid?.max_discharge_rate_kw;

  // Derived Metrics
  const essentialDemand = state.loads
    .filter(l => l.is_essential && l.is_active)
    .reduce((sum, l) => sum + l.current_draw_kw, 0);

  const gridRedline = state.total_generation_kw + 
    state.battery_grid.modules
      .filter(m => m.is_online && m.current_charge_kwh > 0)
      .reduce((sum, m) => sum + m.max_discharge_rate_kw, 0);

  const inverterLoadPct = gridRedline > 0 ? (state.total_demand_kw / gridRedline) * 100 : 0;

  const alertsCount = 
    state.sources.filter(s => !s.is_operational || s.is_manually_disabled).length +
    state.loads.filter(l => !l.is_active || l.is_manually_disabled).length +
    state.battery_grid.modules.filter(m => !m.is_online || m.temperature > 50).length;

  return (
    <section className="space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="h-2.5 w-2.5 rounded-full bg-accent-green animate-pulse" />
        <h2 className="text-lg font-semibold tracking-wide uppercase text-text-secondary flex items-center gap-4">
          HUD — System Overview
          {isBottleneck && (
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-accent-red/20 text-accent-red border border-accent-red/30 animate-pulse">
              INVERTER BOTTLENECK
            </span>
          )}
          {isThermalThrottling && (
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded bg-accent-amber/20 text-accent-amber border border-accent-amber/30 animate-pulse">
              THERMAL THROTTLE
            </span>
          )}
        </h2>
        <span className="ml-auto font-mono text-xs text-text-muted">
          TICK {state.tick.toLocaleString()}
        </span>
      </div>

      {/* Top row: gauge + stats */}
      <div className="flex flex-wrap items-center gap-6">
        <BatteryGauge
          pct={state.battery_grid.charge_pct}
          charge={state.battery_grid.current_charge_kwh}
          max={state.battery_grid.max_capacity_kwh}
          netPower={state.net_power_kw}
        />

        <FrequencyMeter 
          frequency={state.grid_frequency}
          inertia={state.total_inertia}
        />

        <div className="flex flex-wrap gap-3 flex-1">
          <StatCard
            label="Generation"
            value={state.total_generation_kw.toFixed(2)}
            unit="kW"
            accent="var(--accent-cyan)"
          />
          <StatCard
            label="Demand"
            value={state.total_demand_kw.toFixed(2)}
            unit="kW"
            accent="var(--accent-amber)"
          >
             <p className="text-[10px] text-text-muted font-mono uppercase">
               Essential: {essentialDemand.toFixed(1)} kW
             </p>
          </StatCard>
          <StatCard
            label="Grid Redline"
            value={gridRedline.toFixed(1)}
            unit="kW"
            accent="var(--accent-purple)"
          >
             <p className="text-[10px] text-text-muted font-mono uppercase">
               Max Peak Capacity
             </p>
          </StatCard>
          <StatCard
            label="Net Power"
            value={`${netPrefix}${state.net_power_kw.toFixed(2)}`}
            unit="kW"
            accent={netColor}
          >
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-[9px] uppercase font-mono text-text-muted">
                <span>Inverter Load</span>
                <span>{inverterLoadPct.toFixed(0)}%</span>
              </div>
              <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${inverterLoadPct > 90 ? 'bg-accent-red' : 'bg-accent-cyan'}`}
                  style={{ width: `${Math.min(100, inverterLoadPct)}%` }}
                />
              </div>
            </div>
          </StatCard>
          <StatCard
            label="Ess. Uptime"
            value={`${state.global_uptime_pct.toFixed(1)}`}
            unit="%"
            accent={state.global_uptime_pct >= 99.0 ? "var(--accent-green)" : "var(--accent-amber)"}
          />
          <StatCard
            label="Active Alerts"
            value={alertsCount.toString()}
            unit="warnings"
            accent={alertsCount > 0 ? "var(--accent-red)" : "var(--text-muted)"}
          >
             <p className={`text-[10px] font-mono uppercase ${alertsCount > 0 ? 'text-accent-amber animate-pulse' : 'text-text-muted'}`}>
               {alertsCount > 0 ? "System Integrity Compromised" : "All Systems Nominal"}
             </p>
          </StatCard>
          <StatCard
            label="Material Credits"
            value={state.material_credits.toFixed(0)}
            unit="credits"
            accent="var(--accent-amber)"
          >
              <p className="text-[10px] text-text-muted font-mono uppercase">
                Reclaimed Resources
              </p>
          </StatCard>
        </div>
      </div>

      {/* Area chart: generation vs demand */}
      {history.length > 1 && (
        <div className="card p-4">
          <h3 className="text-[11px] uppercase tracking-widest text-text-muted font-mono mb-3">
            Power History (last 60 ticks)
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={history}>
              <defs>
                <linearGradient id="gradGen" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradDemand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#fbbf24" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="tick"
                tick={{ fill: "#64748b", fontSize: 10 }}
                stroke="#1e293b"
              />
              <YAxis
                tick={{ fill: "#64748b", fontSize: 10 }}
                stroke="#1e293b"
                width={40}
              />
              <Tooltip content={<ChartTooltip />} />
              <Area
                type="monotone"
                dataKey="gen"
                name="Generation"
                stroke="#22d3ee"
                fill="url(#gradGen)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="demand"
                name="Demand"
                stroke="#fbbf24"
                fill="url(#gradDemand)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
