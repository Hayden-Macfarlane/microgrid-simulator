// TypeScript types mirroring the backend JSON response

export interface SourceData {
  id: string;
  name: string;
  type: string;
  max_output_kw: number;
  current_output_kw: number;
  is_operational: boolean;
  repair_ticks_remaining: number;
  is_manually_disabled: boolean;
}

export interface LoadData {
  id: string;
  name: string;
  type: string;
  max_draw_kw: number;
  current_draw_kw: number;
  is_essential: boolean;
  is_active: boolean;
  repair_ticks_remaining: number;
  is_manually_disabled: boolean;
}

export interface BatteryModuleData {
  id: string;
  name: string;
  max_capacity_kwh: number;
  current_charge_kwh: number;
  max_charge_rate_kw: number;
  max_discharge_rate_kw: number;
  health_percentage: number;
  temperature: number;
  is_online: boolean;
}

export interface BatteryGridData {
  modules: BatteryModuleData[];
  reserve_unlocked: boolean;
  max_capacity_kwh: number;
  current_charge_kwh: number;
  charge_pct: number;
  max_charge_rate_kw: number;
  max_discharge_rate_kw: number;
}

export interface FaultEntry {
  tick: number;
  type: string;
  target: string;
  detail: string;
}

export interface FaultData {
  fault_probability: number;
  total_faults: number;
  fault_log: FaultEntry[];
}

export interface ShedEvent {
  tick: number;
  loads_shed: string[];
  reason: string;
}

export interface SimulationSettings {
  battery_degradation_rate: number;
  base_failure_chance: number;
  min_repair_ticks: number;
  max_repair_ticks: number;
  shed_threshold: number;
  throttle_threshold: number;
}

export interface GridState {
  tick: number;
  total_ticks: number;
  global_uptime_pct: number;
  total_generation_kw: number;
  total_demand_kw: number;
  net_power_kw: number;
  sources: SourceData[];
  loads: LoadData[];
  battery_grid: BatteryGridData;
  faults: FaultData;
  shed_log: ShedEvent[];
  settings: SimulationSettings;
}
