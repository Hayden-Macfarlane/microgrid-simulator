// Centralized API helper for the microgrid backend

const API_BASE = "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  console.log("FETCHING FROM:", url);
  try {
    const res = await fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", ...options?.headers },
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `API error ${res.status}`);
    }
    return res.json();
  } catch (error) {
    console.error("Detailed Fetch Error:", error);
    throw error;
  }
}

export const api = {
  getState: () => request<import("@/types/grid").GridState>("/grid/state"),

  tick: () => request<import("@/types/grid").GridState>("/grid/tick", { method: "POST" }),

  tickN: (n: number) =>
    request<import("@/types/grid").GridState>(`/grid/tick/${n}`, { method: "POST" }),

  triggerFault: () =>
    request<{ triggered_faults: import("@/types/grid").FaultEntry[]; state: import("@/types/grid").GridState }>(
      "/grid/fault",
      { method: "POST" },
    ),

  restart: () =>
    request<{ message: string; state: import("@/types/grid").GridState }>(
      "/grid/restart",
      { method: "POST" }
    ),

  addSource: (type: string, name: string, maxOutput: number) =>
    request("/grid/source", {
      method: "POST",
      body: JSON.stringify({ type, name, max_output: maxOutput }),
    }),

  addLoad: (type: string, name: string, maxDraw: number, isEssential: boolean) =>
    request("/grid/load", {
      method: "POST",
      body: JSON.stringify({ type, name, max_draw: maxDraw, is_essential: isEssential }),
    }),

  toggleSource: (id: string) =>
    request<{ message: string; is_manually_disabled: boolean }>(`/grid/source/${id}/toggle`, {
      method: "POST",
    }),

  toggleLoad: (id: string) =>
    request<{ message: string; is_manually_disabled: boolean }>(`/grid/load/${id}/toggle`, {
      method: "POST",
    }),

  addBatteryModule: (name: string, maxCapacity: number, maxChargeRate: number, maxDischargeRate: number) =>
    request("/grid/battery/module", {
      method: "POST",
      body: JSON.stringify({
        name,
        max_capacity: maxCapacity,
        max_charge_rate: maxChargeRate,
        max_discharge_rate: maxDischargeRate,
      }),
    }),

  toggleBatteryReserve: () =>
    request<{ message: string; reserve_unlocked: boolean }>("/grid/battery/toggle-reserve", {
      method: "POST",
    }),

  toggleBatteryModule: (id: string) =>
    request<{ message: string; is_online: boolean }>(`/grid/battery/module/${id}/toggle`, {
      method: "POST",
    }),

  toggleAutoTick: () =>
    request<{ auto_tick: boolean; message: string }>("/grid/auto-tick", { method: "POST" }),

  autoTickStatus: () =>
    request<{ auto_tick: boolean }>("/grid/auto-tick/status"),

  updateSettings: (settings: import("@/types/grid").SimulationSettings) =>
    request("/grid/settings", {
      method: "POST",
      body: JSON.stringify(settings),
    }),
};
