"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { GridState } from "@/types/grid";
import HUD from "@/components/HUD";
import ComponentRoster from "@/components/ComponentRoster";
import CommandCenter from "@/components/CommandCenter";
import FaultLog from "@/components/FaultLog";
import SimulationSettingsPanel from "@/components/SimulationSettingsPanel";
import BatterySubstation from "@/components/BatterySubstation";
import EnvironmentPanel from "@/components/EnvironmentPanel";

const MAX_HISTORY = 60;

export default function Dashboard() {
  const [state, setState] = useState<GridState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoTick, setAutoTick] = useState(false);
  const [history, setHistory] = useState<
    { tick: number; gen: number; demand: number; net: number }[]
  >([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* ---- Fetch grid state ---- */
  const fetchState = useCallback(async () => {
    try {
      const s = await api.getState();
      setState(s);
      setError(null);
      setHistory((prev) => {
        const entry = {
          tick: s.tick,
          gen: s.total_generation_kw,
          demand: s.total_demand_kw,
          net: s.net_power_kw,
        };
        // Avoid duplicate ticks
        if (prev.length > 0 && prev[prev.length - 1].tick === s.tick) return prev;
        const next = [...prev, entry];
        return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
      });
    } catch (err: any) {
      console.error("Failed to fetch grid state:", err);
      setError(err.message || "Failed to connect to backend");
    }
  }, []);

  /* ---- Poll every 1 second ---- */
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchState(); // initial
    intervalRef.current = setInterval(fetchState, 1000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchState]);

  /* ---- Auto-tick toggle ---- */
  const handleAutoTickToggle = async () => {
    try {
      const res = await api.toggleAutoTick();
      setAutoTick(res.auto_tick);
    } catch (err) {
      console.error(err);
    }
  };

  /* ---- Manual tick ---- */
  const handleManualTick = async () => {
    try {
      const s = await api.tick();
      setState(s);
    } catch (err) {
      console.error(err);
    }
  };

  /* ---- Fault inject ---- */
  const handleFault = async () => {
    try {
      const res = await api.triggerFault();
      setState(res.state);
    } catch (err) {
      console.error(err);
    }
  };

  /* ---- Restart Grid ---- */
  const handleRestart = async () => {
    // If auto-tick is running, stop it
    if (autoTick) {
      await api.toggleAutoTick();
      setAutoTick(false);
    }
    try {
      const res = await api.restart();
      setState(res.state);
      setHistory([]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <main className="min-h-screen p-6 lg:p-10 max-w-[1440px] mx-auto space-y-8">
      {/* Title bar */}
      <header className="flex items-center gap-4 border-b border-border-subtle pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent-cyan/15 flex items-center justify-center text-xl">
            ⚡
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-text-primary">
              Microgrid Simulator
            </h1>
            <p className="text-xs text-text-muted font-mono uppercase tracking-wider">
              Mission Control Dashboard
            </p>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-3">
          {autoTick && (
            <span className="flex items-center gap-2 text-xs font-mono text-accent-green">
              <span className="w-2 h-2 bg-accent-green rounded-full animate-pulse" />
              LIVE
            </span>
          )}
          <span className="font-mono text-xs text-text-muted">
            v0.1.0
          </span>
        </div>
      </header>

      {/* Error State */}
      {error && (
        <div className="bg-accent-red/10 border border-accent-red/20 rounded-xl p-4 flex items-center gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="w-10 h-10 rounded-full bg-accent-red/20 flex items-center justify-center text-accent-red">
            ⚠️
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-bold text-accent-red">System Connection Error</h3>
            <p className="text-xs text-text-muted mt-0.5">
              CRITICAL: Cannot connect to backend at <code className="bg-black/20 px-1 rounded">http://127.0.0.1:8000</code>. 
              Details: {error}
            </p>
          </div>
          <button 
            onClick={() => fetchState()}
            className="px-4 py-2 bg-accent-red text-white text-xs font-bold rounded-lg hover:brightness-110 transition-all active:scale-95"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Dashboard sections */}
      <EnvironmentPanel state={state?.environment} />
      <HUD state={state} history={history} />
      <ComponentRoster
        sources={state?.sources || []}
        loads={state?.loads || []}
        environment={state?.environment}
        onRefresh={fetchState}
      />
      {state?.battery_grid && (
        <BatterySubstation
          batteryGrid={state.battery_grid}
          onRefresh={fetchState}
        />
      )}
      <CommandCenter
        autoTick={autoTick}
        onAutoTickToggle={handleAutoTickToggle}
        onManualTick={handleManualTick}
        onFault={handleFault}
        onRestart={handleRestart}
        onRefresh={fetchState}
      />
      <SimulationSettingsPanel
        settings={state?.settings}
        onRefresh={fetchState}
      />
      <FaultLog
        faults={state?.faults.fault_log || []}
        sheds={state?.shed_log || []}
      />
    </main>
  );
}
