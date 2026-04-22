"use client";

import { FaultEntry, ShedEvent } from "@/types/grid";
import { useRef, useEffect } from "react";

interface FaultLogProps {
  faults: FaultEntry[];
  sheds: ShedEvent[];
}

export default function FaultLog({ faults, sheds }: FaultLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Merge faults and sheds into a single timeline sorted by tick
  const events = [
    ...faults.map((f) => ({
      tick: f.tick,
      type: f.type,
      message: f.detail,
      severity: "fault" as const,
    })),
    ...sheds.map((s) => ({
      tick: s.tick,
      type: "load_shed",
      message: `${s.loads_shed.join(", ")} shed — ${s.reason}`,
      severity: "warning" as const,
    })),
  ].sort((a, b) => b.tick - a.tick); // newest first

  // Auto-scroll to top on new events
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [events.length]);

  const severityColor = {
    fault: "text-accent-red",
    warning: "text-accent-amber",
  };

  const typeLabels: Record<string, string> = {
    source_outage: "SRC_OUTAGE",
    load_failure: "LOAD_FAIL",
    battery_degradation: "BATT_DEGRAD",
    load_shed: "LOAD_SHED",
  };

  return (
    <section className="space-y-4 animate-fade-in">
      <h2 className="text-lg font-semibold tracking-wide uppercase text-text-secondary flex items-center gap-3">
        <span className="inline-block h-2.5 w-2.5 rounded-full bg-accent-red" />
        Event Log
      </h2>

      <div
        ref={scrollRef}
        className="card p-4 h-[220px] overflow-y-auto font-mono text-xs space-y-1"
        style={{ background: "rgba(10, 14, 26, 0.8)" }}
      >
        {events.length === 0 ? (
          <p className="text-text-muted text-center py-8">
            No events recorded. The grid is nominal. ✓
          </p>
        ) : (
          events.map((ev, i) => (
            <div
              key={`${ev.tick}-${ev.type}-${i}`}
              className="flex gap-3 leading-relaxed animate-slide-in"
            >
              <span className="text-text-muted shrink-0 w-16 text-right">
                T+{ev.tick}
              </span>
              <span
                className={`shrink-0 w-28 uppercase ${severityColor[ev.severity]}`}
              >
                [{typeLabels[ev.type] || ev.type}]
              </span>
              <span className="text-text-secondary">{ev.message}</span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
