"""
grid_controller.py — Central simulation engine that orchestrates power
generation, consumption, storage, and fault injection each tick.
"""

from __future__ import annotations

from typing import Optional

from app.models.power_source import PowerSource
from app.models.power_load import PowerLoad
from app.models.energy_storage import BatteryGrid
from app.models.fault_injection import FaultInjector
from app.models.settings import SimulationSettings
from app.models.environment_engine import EnvironmentEngine
from dataclasses import asdict


class GridController:
    """
    The 'brain' of the microgrid. Each call to tick() simulates one minute:
      1. Inject faults (stochastic)
      2. Update all sources and loads
      3. Balance generation vs. demand via storage
      4. Shed non-essential loads if deficit remains
    """

    def __init__(
        self,
        sources: list[PowerSource],
        loads: list[PowerLoad],
        battery_grid: BatteryGrid,
        fault_injector: FaultInjector | None = None,
        settings: SimulationSettings | None = None,
    ) -> None:
        self.sources = sources
        self.loads = loads
        self.battery_grid = battery_grid
        self.settings = settings
        self.fault_injector = fault_injector or FaultInjector(settings=settings)
        self.env_engine = EnvironmentEngine()
        self.current_tick: int = 0
        self.total_ticks: int = 0
        self.ticks_fully_powered_essentials: int = 0
        self._shed_log: list[dict] = []
        self._current_env_state = self.env_engine.state
        self._last_line_loss: float = 0.0
        self.material_credits: float = 0.0

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------

    def tick(self) -> dict:
        """Advance the simulation by one minute. Returns the new state."""
        # 1. Sync global SOC settings to battery modules
        if self.settings:
            for m in self.battery_grid.modules:
                m.user_soc_min = self.settings.user_soc_min
                m.user_soc_max = self.settings.user_soc_max

        # 2. Fault injection
        new_faults = self.fault_injector.inject(
            self.current_tick, self.sources, self.loads, self.battery_grid,
        )

        self.current_tick += 1
        self.total_ticks += 1

        self._current_env_state = self.env_engine.tick(self.current_tick)

        # 3. Identify maintenance projects and calculate extra load
        hub = next((l for l in self.loads if l.id == 'l9'), None)
        active_maint_draw = 0.0
        
        scrapping_batteries = [m for m in self.battery_grid.modules if m.is_scrapping]
        repairing_batteries = [m for m in self.battery_grid.modules if m.is_repairing]
        cleaning_panels = [s for s in self.sources if getattr(s, 'is_cleaning', False)]

        if scrapping_batteries:
            active_maint_draw += 30.0
        if repairing_batteries:
            active_maint_draw += 20.0
        if cleaning_panels:
            active_maint_draw += 20.0

        # Update every source and load with env state
        for source in self.sources:
            source.update(self.current_tick, self._current_env_state)
        for load in self.loads:
            load.is_grid_throttled = False
            load.update(self.current_tick, self._current_env_state)
            # Inject maintenance load into Hub
            if load.id == 'l9' and active_maint_draw > 0:
                load.current_draw += active_maint_draw

        # 3. Energy balance
        total_generation = sum(s.current_output for s in self.sources)
        
        # Calculate essential baseline
        essential_demand = sum(l.current_draw for l in self.loads if l.is_active and getattr(l, 'is_essential', False))
        
        # 3. Policy-Based Load Balancing (Shedding/Throttling based on Battery Charge)
        battery_pct = self.battery_grid.to_dict()["charge_pct"] / 100.0
        shed_threshold = self.settings.shed_threshold if self.settings else 0.10
        throttle_threshold = self.settings.throttle_threshold if self.settings else 0.20

        non_essential_loads = [
            l for l in self.loads 
            if l.is_active 
            and not getattr(l, 'is_essential', False)
            and not getattr(l, 'is_manually_disabled', False)
        ]
        
        # --- APPLY POLICY ---
        if battery_pct < shed_threshold:
            # SHED MODE: All non-essentials killed to preserve battery
            for load in non_essential_loads:
                load.current_draw = 0.0
        elif battery_pct < throttle_threshold:
            # THROTTLE MODE: Dynamically matching loads to generation to stay at Net 0.0
            available_for_non_essentials = max(0.0, total_generation - essential_demand)
            total_max_non_essential = sum(l.max_draw for l in non_essential_loads)
            
            if total_max_non_essential > 0:
                # Calculate ratio to match exactly the available generation
                ratio = min(1.0, available_for_non_essentials / total_max_non_essential)
                for load in non_essential_loads:
                    load.current_draw = load.max_draw * ratio
                    if ratio < 1.0:
                        load.is_grid_throttled = True
            else:
                for load in non_essential_loads:
                    load.current_draw = 0.0
                    load.is_grid_throttled = True
        else:
            # NORMAL MODE: Run non-essentials at 100% capacity
            pass

        # 4. Energy balance (Battery as Buffer with Inverter Loss)
        total_demand = sum(l.current_draw for l in self.loads if getattr(l, "is_active", False))
        
        # --- TRANSMISSION LINE LOSS ---
        bus_flow = total_generation
        line_loss = 0.0
        if bus_flow > 500.0:
            line_loss = 0.0001 * (bus_flow - 500.0)**2
        
        self._last_line_loss = line_loss
        net_power = total_generation - total_demand - line_loss

        # 5. Process Maintenance Progress (Only if Hub is receiving full power)
        hub_is_powered = False
        if hub and hub.is_active:
            # Check if hub is receiving its requested power (baseline + maintenance)
            if hub.current_draw >= (hub.max_draw + active_maint_draw) * 0.98:
                hub_is_powered = True

        if hub_is_powered:
            # Process Scrap (50 ticks)
            for m in scrapping_batteries:
                m.scrap_progress += 1
                if m.scrap_progress >= 50:
                    self.battery_grid.modules.remove(m)
                    self.material_credits += 50.0  # One-time material credit
            
            # Process Cleaning (Immediate)
            for s in cleaning_panels:
                if hasattr(s, 'dust_coverage'):
                    s.dust_coverage = 0.0
                if hasattr(s, 'is_cleaning'):
                    s.is_cleaning = False
            
            # Process Repair (Energy Debt)
            # 20kW tool = 0.333 kWh per minute tick
            repair_rate = 20.0 / 60.0
            for m in repairing_batteries:
                m.energy_debt = max(0.0, m.energy_debt - repair_rate)
                if m.energy_debt <= 0:
                    m.health_percentage = 100.0
                    m.is_repairing = False
                    m.is_destroyed = False
                    m.is_online = True

        energy_stored = 0.0
        energy_discharged = 0.0
        remaining_deficit = 0.0

        INVERTER_EFFICIENCY = 0.94

        if net_power >= 0:
            # Excess power → charge battery (Inverter Loss during AC->DC)
            # Battery receives net_power * 0.94
            energy_stored = self.battery_grid.charge(net_power * INVERTER_EFFICIENCY)
        else:
            # Deficit → Drain battery buffer (Inverter Loss during DC->AC)
            deficit = abs(net_power)
            # To provide 'deficit' to the grid, we must pull 'deficit / 0.94' from cells
            raw_discharged = self.battery_grid.discharge(deficit / INVERTER_EFFICIENCY)
            # What actually reaches the grid is the AC-converted power
            energy_discharged = raw_discharged * INVERTER_EFFICIENCY
            remaining_deficit = deficit - energy_discharged

            # 5. Last Resort Shedding (Blackout / Grid Redline)
            # If battery is empty or bottlenecked, we MUST shed more to prevent negative Net Power
            if remaining_deficit > 0:
                extra_loads_shed = []
                # First try to kill non-essentials that survived the policy (if any)
                for load in non_essential_loads:
                    if remaining_deficit <= 0.01: # allow tiny floating point error
                        break
                    if load.current_draw > 0:
                        shed_amount = min(load.current_draw, remaining_deficit)
                        load.current_draw -= shed_amount
                        remaining_deficit -= shed_amount
                        extra_loads_shed.append(load.name)
                
                # Finally, cut essential loads if still imbalanced (True Blackout)
                if remaining_deficit > 0.01:
                    for load in self.loads:
                        if remaining_deficit <= 0.01:
                            break
                        if load.is_active and getattr(load, 'is_essential', False) and load.current_draw > 0:
                            actual_cut = min(load.current_draw, remaining_deficit)
                            load.current_draw -= actual_cut
                            remaining_deficit -= actual_cut
                            extra_loads_shed.append(load.name)

                if extra_loads_shed:
                     self._shed_log.append({
                        "tick": self.current_tick,
                        "loads_shed": list(set(extra_loads_shed)),
                        "reason": "Insufficient generation and maxed-out battery reserves.",
                     })

        # Check uptime logic
        essentials_powered = True
        if remaining_deficit > 0:
            # If after shedding all non-essentials there is STILL a deficit, we failed essentials
            essentials_powered = False
            
        # Also check if any essential load is offline due to a fault or override
        if any((not l.is_active or l.current_draw == 0.0) for l in self.loads if l.is_essential):
            essentials_powered = False

        if essentials_powered:
            self.ticks_fully_powered_essentials += 1

        # 6. Thermal Framework & Battery Physics
        heating_active = any(l.name == "Active Heating" and l.current_draw > 0 for l in self.loads)
        cooling_active = any(l.name == "Active Cooling" and l.current_draw > 0 for l in self.loads)
        
        deg_rate = self.settings.battery_degradation_rate if self.settings else 0.05
        self.battery_grid.tick(
            degradation_rate=deg_rate,
            env_temp=self._current_env_state.current_temperature,
            heating_active=heating_active,
            cooling_active=cooling_active
        )

        return self.get_state()

    def tick_multiple(self, n: int) -> dict:
        """Advance by n ticks, return final state."""
        for _ in range(n):
            self.tick()
        return self.get_state()

    def force_fault(self) -> dict:
        """Manually trigger a guaranteed fault. Returns new faults + state."""
        faults = self.fault_injector.force_inject(
            self.current_tick, self.sources, self.loads, self.battery_grid,
        )
        return {
            "triggered_faults": faults,
            "state": self.get_state(),
        }

    # ------------------------------------------------------------------
    # Dynamic component management
    # ------------------------------------------------------------------

    def add_source(self, source: PowerSource) -> dict:
        """Add a new power source to the grid."""
        self.sources.append(source)
        return source.to_dict()

    def add_load(self, load: PowerLoad) -> dict:
        """Add a new power load to the grid."""
        self.loads.append(load)
        return load.to_dict()

    # ------------------------------------------------------------------
    # State snapshot
    # ------------------------------------------------------------------

    def get_state(self) -> dict:
        total_generation = sum(s.current_output for s in self.sources)
        total_demand = sum(l.current_draw for l in self.loads if getattr(l, "is_active", False))

        uptime_pct = 0.0
        if self.total_ticks > 0:
            uptime_pct = (self.ticks_fully_powered_essentials / self.total_ticks) * 100.0

        return {
            "tick": self.current_tick,
            "total_ticks": self.total_ticks,
            "global_uptime_pct": round(uptime_pct, 2),
            "settings": self.settings.to_dict() if self.settings else {},
            "environment": asdict(self._current_env_state),
            "total_generation_kw": round(total_generation, 4),
            "total_demand_kw": round(total_demand, 4),
            "net_power_kw": round(total_generation - total_demand, 4),
            "transmission_loss_kw": round(float(getattr(self, '_last_line_loss', 0.0)), 4),
            "sources": [s.to_dict() for s in self.sources],
            "loads": [l.to_dict() for l in self.loads],
            "battery_grid": self.battery_grid.to_dict(),
            "faults": self.fault_injector.to_dict(),
            "shed_log": self._shed_log,
            "material_credits": round(self.material_credits, 2),
        }
