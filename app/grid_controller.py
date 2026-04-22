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
        self.current_tick: int = 0
        self.total_ticks: int = 0
        self.ticks_fully_powered_essentials: int = 0
        self._shed_log: list[dict] = []

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

        # 2. Update every source and load
        for source in self.sources:
            source.update(self.current_tick)
        for load in self.loads:
            load.update(self.current_tick)

        # 3. Energy balance
        total_generation = sum(s.current_output for s in self.sources)
        
        deg_rate = self.settings.battery_degradation_rate if self.settings else 0.05
        self.battery_grid.tick(degradation_rate=deg_rate)
        
        # Calculate essential baseline
        essential_demand = sum(l.current_draw for l in self.loads if l.is_active and getattr(l, 'is_essential', False))
        
        # Determine battery state
        battery_pct = self.battery_grid.to_dict()["charge_pct"] / 100.0

        shed_threshold = self.settings.shed_threshold if self.settings else 0.10
        throttle_threshold = self.settings.throttle_threshold if self.settings else 0.20

        non_essential_loads = [
            l for l in self.loads 
            if l.is_active 
            and not getattr(l, 'is_essential', False)
            and not getattr(l, 'is_manually_disabled', False)
        ]
        max_non_essential_draw = sum(l.max_draw for l in non_essential_loads)

        loads_shed: list[str] = []

        if battery_pct < shed_threshold:
            # Shed State: all non-essential loads dropped to 0
            for load in non_essential_loads:
                if load.current_draw > 0.0:
                    loads_shed.append(load.name)
                load.current_draw = 0.0
            if loads_shed:
                self._shed_log.append({
                    "tick": self.current_tick,
                    "loads_shed": loads_shed,
                    "reason": f"Battery critically low ({battery_pct*100:.1f}%). Shedding all non-essential loads.",
                })
        elif battery_pct < throttle_threshold:
            # Throttle State: distribute remaining generation among non-essential loads
            available_power = total_generation - essential_demand
            if available_power <= 0:
                for load in non_essential_loads:
                    load.current_draw = 0.0
            elif max_non_essential_draw > 0:
                ratio = min(1.0, available_power / max_non_essential_draw)
                for load in non_essential_loads:
                    # Dynamically throttle
                    load.current_draw = load.max_draw * ratio
        else:
            # Normal State: non-essential loads draw max_draw
            pass # update() already sets them to their calculated max_draw

        # Re-calc overall demand
        total_demand = sum(l.current_draw for l in self.loads if getattr(l, "is_active", False))
        surplus = total_generation - total_demand

        energy_stored = 0.0
        energy_discharged = 0.0
        remaining_deficit = 0.0

        if surplus >= 0:
            # Excess power → charge battery
            energy_stored = self.battery_grid.charge(surplus)
        else:
            # Deficit → try to discharge battery
            deficit = abs(surplus)
            energy_discharged = self.battery_grid.discharge(deficit)
            remaining_deficit = deficit - energy_discharged

            # If we STILL have a deficit (battery empty, throttling not enough because generation dropped too fast)
            # Hard shed to balance equation
            if remaining_deficit > 0:
                extra_loads_shed = []
                for load in non_essential_loads:
                    if remaining_deficit <= 0:
                        break
                    if load.current_draw > 0:
                        remaining_deficit -= load.current_draw
                        load.current_draw = 0.0
                        extra_loads_shed.append(load.name)
                if extra_loads_shed:
                     self._shed_log.append({
                        "tick": self.current_tick,
                        "loads_shed": extra_loads_shed,
                        "reason": "Insufficient generation and empty battery reserves.",
                     })

                # If STILL a deficit, cut essential loads (Total Blackout)
                if remaining_deficit > 0:
                    for load in self.loads:
                        if remaining_deficit <= 0:
                            break
                        if load.is_active and getattr(load, 'is_essential', False) and load.current_draw > 0:
                            actual_cut = min(load.current_draw, remaining_deficit)
                            load.current_draw -= actual_cut
                            remaining_deficit -= actual_cut

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
            "total_generation_kw": round(total_generation, 4),
            "total_demand_kw": round(total_demand, 4),
            "net_power_kw": round(total_generation - total_demand, 4),
            "sources": [s.to_dict() for s in self.sources],
            "loads": [l.to_dict() for l in self.loads],
            "battery_grid": self.battery_grid.to_dict(),
            "faults": self.fault_injector.to_dict(),
            "shed_log": self._shed_log,
        }
