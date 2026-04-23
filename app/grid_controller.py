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

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------

    def tick(self) -> dict:
        """Advance the simulation by one minute. Returns the new state."""
        self.current_tick += 1
        self.total_ticks += 1

        # 1. Fault injection
        new_faults = self.fault_injector.inject(
            self.current_tick, self.sources, self.loads, self.battery_grid,
        )

        # 2. Update environment
        self._current_env_state = self.env_engine.tick(self.current_tick)

        # 3. Update every source and load with env state
        for source in self.sources:
            source.update(self.current_tick, self._current_env_state)
        for load in self.loads:
            load.is_grid_throttled = False
            load.update(self.current_tick, self._current_env_state)

        # 3. Energy balance
        total_generation = sum(s.current_output for s in self.sources)
        
        # (Battery grid tick moved to end to capture HVAC power state)
        
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
            # (already set by load.update() above)
            pass

        # 4. Energy balance (Battery as Buffer)
        total_demand = sum(l.current_draw for l in self.loads if getattr(l, "is_active", False))
        net_power = total_generation - total_demand

        energy_stored = 0.0
        energy_discharged = 0.0
        remaining_deficit = 0.0

        if net_power >= 0:
            # Excess power → charge battery
            energy_stored = self.battery_grid.charge(net_power)
        else:
            # Deficit → Drain battery buffer
            deficit = abs(net_power)
            energy_discharged = self.battery_grid.discharge(deficit)
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
            "sources": [s.to_dict() for s in self.sources],
            "loads": [l.to_dict() for l in self.loads],
            "battery_grid": self.battery_grid.to_dict(),
            "faults": self.fault_injector.to_dict(),
            "shed_log": self._shed_log,
        }
