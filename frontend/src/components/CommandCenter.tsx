"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface CommandCenterProps {
  autoTick: boolean;
  onAutoTickToggle: () => void;
  onManualTick: () => void;
  onFault: () => void;
  onRestart: () => void;
  onRefresh: () => void;
}

/* ------------------------------------------------------------------ */
/* Add Source Form                                                      */
/* ------------------------------------------------------------------ */
function AddSourceForm({ onRefresh }: { onRefresh: () => void }) {
  const [type, setType] = useState("SolarPanel");
  const [name, setName] = useState("");
  const [maxOutput, setMaxOutput] = useState(30);
  const [loading, setLoading] = useState(false);

  const defaults: Record<string, { name: string; output: number }> = {
    SolarPanel: { name: "Solar Array", output: 50 },
    WindTurbine: { name: "Wind Turbine", output: 30 },
    RTG: { name: "RTG Unit", output: 10 },
  };

  const handleTypeChange = (t: string) => {
    setType(t);
    if (!name || Object.values(defaults).some((d) => d.name === name)) {
      setName(defaults[t]?.name || "");
    }
    setMaxOutput(defaults[t]?.output || 30);
  };

  const submit = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      await api.addSource(type, name.trim(), maxOutput);
      setName(defaults[type]?.name || "");
      onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-4 space-y-3">
      <h3 className="text-[11px] uppercase tracking-widest text-text-muted font-mono">
        ⚡ Add Power Source
      </h3>
      <div className="grid grid-cols-3 gap-2">
        {Object.keys(defaults).map((t) => (
          <button
            key={t}
            onClick={() => handleTypeChange(t)}
            className={`text-xs font-mono py-2 px-2 rounded-lg border transition-all ${
              type === t
                ? "border-accent-cyan bg-accent-cyan/10 text-accent-cyan"
                : "border-border-subtle text-text-muted hover:border-border-glow"
            }`}
          >
            {t === "SolarPanel" ? "☀️" : t === "WindTurbine" ? "💨" : "⚛️"} {t}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name"
          className="flex-1 bg-bg-secondary border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-cyan transition-colors"
        />
        <input
          type="number"
          value={maxOutput}
          onChange={(e) => setMaxOutput(Number(e.target.value))}
          min={1}
          className="w-20 bg-bg-secondary border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-cyan transition-colors font-mono"
        />
        <span className="self-center text-xs text-text-muted">kW</span>
      </div>
      <button
        onClick={submit}
        disabled={loading || !name.trim()}
        className="w-full py-2 rounded-lg bg-accent-cyan/20 text-accent-cyan text-sm font-semibold hover:bg-accent-cyan/30 border border-accent-cyan/30 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {loading ? "Adding…" : "Add Source"}
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Add Load Form                                                        */
/* ------------------------------------------------------------------ */
function AddLoadForm({ onRefresh }: { onRefresh: () => void }) {
  const [type, setType] = useState("Heater");
  const [name, setName] = useState("Habitat Heater");
  const [draw, setDraw] = useState(15);
  const [essential, setEssential] = useState(false);
  const [loading, setLoading] = useState(false);

  const defaults: Record<string, { name: string; draw: number; essential: boolean }> = {
    LifeSupport: { name: "Life Support", draw: 20, essential: true },
    Heater: { name: "Habitat Heater", draw: 15, essential: false },
    Lighting: { name: "Interior Lighting", draw: 5, essential: false },
  };

  const handleTypeChange = (t: string) => {
    setType(t);
    if (!name || Object.values(defaults).some((d) => d.name === name)) {
      setName(defaults[t]?.name || "");
    }
    setDraw(defaults[t]?.draw || 10);
    setEssential(defaults[t]?.essential || false);
  };

  const submit = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      await api.addLoad(type, name.trim(), draw, essential);
      setName(defaults[type]?.name || "");
      onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-4 space-y-3">
      <h3 className="text-[11px] uppercase tracking-widest text-text-muted font-mono">
        🔌 Add Power Load
      </h3>
      <div className="grid grid-cols-3 gap-2">
        {Object.keys(defaults).map((t) => (
          <button
            key={t}
            onClick={() => handleTypeChange(t)}
            className={`text-xs font-mono py-2 px-2 rounded-lg border transition-all ${
              type === t
                ? "border-accent-amber bg-accent-amber/10 text-accent-amber"
                : "border-border-subtle text-text-muted hover:border-border-glow"
            }`}
          >
            {t === "LifeSupport" ? "❤️" : t === "Heater" ? "🔥" : "💡"} {t}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name"
          className="flex-1 bg-bg-secondary border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-amber transition-colors"
        />
        <input
          type="number"
          value={draw}
          onChange={(e) => setDraw(Number(e.target.value))}
          min={1}
          className="w-20 bg-bg-secondary border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-amber transition-colors font-mono"
        />
        <span className="self-center text-xs text-text-muted">kW</span>
      </div>
      <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
        <input
          type="checkbox"
          checked={essential}
          onChange={(e) => setEssential(e.target.checked)}
          className="w-4 h-4 rounded border-border-subtle accent-accent-amber"
        />
        Mark as essential (cannot be shed)
      </label>
      <button
        onClick={submit}
        disabled={loading || !name.trim()}
        className="w-full py-2 rounded-lg bg-accent-amber/20 text-accent-amber text-sm font-semibold hover:bg-accent-amber/30 border border-accent-amber/30 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {loading ? "Adding…" : "Add Load"}
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Add Battery Module Form                                              */
/* ------------------------------------------------------------------ */
function AddBatteryModuleForm({ onRefresh }: { onRefresh: () => void }) {
  const [name, setName] = useState("Expansion Module");
  const [capacity, setCapacity] = useState(250);
  const [rate, setRate] = useState(30);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      await api.addBatteryModule(name.trim(), capacity, rate, rate);
      setName("Expansion Module " + Math.floor(Math.random() * 100));
      onRefresh();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-4 space-y-3 lg:col-span-2">
      <h3 className="text-[11px] uppercase tracking-widest text-text-muted font-mono">
        🔋 Add Battery Module
      </h3>
      <div className="flex flex-wrap gap-2">
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Module Name"
          className="flex-1 bg-bg-secondary border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-green transition-colors"
        />
        <div className="flex items-center bg-bg-secondary border border-border-subtle rounded-lg pl-2 overflow-hidden focus-within:border-accent-green transition-colors max-w-[120px]">
          <input
            type="number"
            value={capacity}
            onChange={(e) => setCapacity(Number(e.target.value))}
            min={10}
            className="w-12 bg-transparent py-2 text-sm text-text-primary focus:outline-none font-mono"
            placeholder="Cap"
          />
          <span className="text-xs text-text-muted pr-2">kWh Max</span>
        </div>
        <div className="flex items-center bg-bg-secondary border border-border-subtle rounded-lg pl-2 overflow-hidden focus-within:border-accent-green transition-colors max-w-[120px]">
          <input
            type="number"
            value={rate}
            onChange={(e) => setRate(Number(e.target.value))}
            min={5}
            className="w-12 bg-transparent py-2 text-sm text-text-primary focus:outline-none font-mono"
            placeholder="Rate"
          />
          <span className="text-xs text-text-muted pr-2">kW I/O</span>
        </div>
        <button
          onClick={submit}
          disabled={loading || !name.trim()}
          className="px-4 py-2 rounded-lg bg-accent-green/20 text-accent-green text-sm font-semibold hover:bg-accent-green/30 border border-accent-green/30 transition-all disabled:opacity-40"
        >
          {loading ? "…" : "Deploy"}
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main Command Center                                                  */
/* ------------------------------------------------------------------ */
export default function CommandCenter({
  autoTick,
  onAutoTickToggle,
  onManualTick,
  onFault,
  onRestart,
  onRefresh,
}: CommandCenterProps) {
  return (
    <section className="space-y-4 animate-fade-in">
      <h2 className="text-lg font-semibold tracking-wide uppercase text-text-secondary flex items-center gap-3">
        <span className="inline-block h-2.5 w-2.5 rounded-full bg-accent-amber" />
        Command Center
      </h2>

      {/* Control buttons row */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Restart Sim */}
        <button
          onClick={onRestart}
          className="px-5 py-2.5 rounded-lg border border-border-subtle bg-bg-secondary text-text-primary font-mono text-sm font-semibold hover:border-accent-cyan transition-all"
        >
          🔄 Restart Sim
        </button>

        {/* Auto-tick toggle */}
        <button
          onClick={onAutoTickToggle}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg border font-mono text-sm font-semibold transition-all ${
            autoTick
              ? "border-accent-green bg-accent-green/15 text-accent-green"
              : "border-border-subtle text-text-muted hover:border-border-glow"
          }`}
        >
          {autoTick ? "⏸ Pause" : "▶ Play"} Auto-Tick
        </button>

        {/* Manual tick */}
        <button
          onClick={onManualTick}
          className="px-5 py-2.5 rounded-lg border border-border-subtle text-text-secondary font-mono text-sm font-semibold hover:border-accent-cyan hover:text-accent-cyan transition-all"
        >
          ⏭ Tick +1
        </button>

        {/* Toggle Reserve */}
        <button
          onClick={async () => { await api.toggleBatteryReserve(); onRefresh(); }}
          className="px-5 py-2.5 rounded-lg border border-accent-amber/50 text-accent-amber font-mono text-sm font-semibold hover:bg-accent-amber/10 transition-all"
        >
          🔓 Toggle Reserve
        </button>

        {/* FAULT INJECT (big red button) */}
        <button
          onClick={onFault}
          className="ml-auto px-8 py-2.5 rounded-lg bg-accent-red/20 text-accent-red border-2 border-accent-red/50 font-bold text-sm uppercase tracking-wider hover:bg-accent-red/30 animate-pulse-glow transition-all"
        >
          ⚠ Inject Fault
        </button>
      </div>

      {/* Forms */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AddSourceForm onRefresh={onRefresh} />
        <AddLoadForm onRefresh={onRefresh} />
        <AddBatteryModuleForm onRefresh={onRefresh} />
      </div>
    </section>
  );
}
