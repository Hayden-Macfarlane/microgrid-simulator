"""
fault_injection.py — Randomly injects faults into grid components to
simulate real-world failures (source outages, load failures, battery
degradation).
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .power_source import PowerSource
    from .power_load import PowerLoad
    from .energy_storage import BatteryGrid
    from .settings import SimulationSettings

class FaultInjector:
    """Stochastic fault injection engine for the microgrid simulation."""

    def __init__(self, settings: SimulationSettings | None = None) -> None:
        """
        Args:
            settings: SimulationSettings to define failure probabilities and repairs
        """
        self.settings = settings
        self.fault_log: list[dict] = []

    # ------------------------------------------------------------------
    # Core injection
    # ------------------------------------------------------------------

    def inject(
        self,
        tick: int,
        sources: list[PowerSource],
        loads: list[PowerLoad],
        battery_grid: BatteryGrid,
    ) -> list[dict]:
        """Run fault checks for one tick. Returns list of new faults."""
        new_faults: list[dict] = []

        # Fallback to probability if missing
        raw_prob = self.settings.base_failure_chance if self.settings else 1.0
        # Divide by 1000.0 instead of 100.0 to effectively nerf base probability by 10x
        prob = raw_prob / 1000.0
        
        min_rep = self.settings.min_repair_ticks if self.settings else 5
        max_rep = self.settings.max_repair_ticks if self.settings else 15
        deg_rate = self.settings.battery_degradation_rate if self.settings else 0.10
        
        # --- Source outage ---
        for target in sources:
            if target.is_operational and target.repair_ticks_remaining == 0:
                if random.random() < prob:
                    target.is_operational = False
                    target.current_output = 0.0
                    repair_time = random.randint(min_rep, max_rep)
                    target.repair_ticks_remaining = repair_time
                    fault = {
                        "tick": tick,
                        "type": "source_outage",
                        "target": target.name,
                        "detail": f"{target.name} has gone offline. Repair time: {repair_time} ticks.",
                    }
                    new_faults.append(fault)


        # --- Battery degradation (lose fixed rate based on setting % of current max) ---
        for target in battery_grid.modules:
            if target.is_online:
                if random.random() < prob:
                    # Injected fault results in a one-time health percentage drop
                    lost_health = deg_rate
                    target.health_percentage = max(0.0, target.health_percentage - lost_health)
                    target.current_charge = min(target.current_charge, target.max_capacity)
                    fault = {
                        "tick": tick,
                        "type": "battery_degradation",
                        "target": target.name,
                        "detail": (
                            f"{target.name} suffered a fault and lost {lost_health:.1f}% health. "
                            f"New health: {target.health_percentage:.1f}%."
                        ),
                    }
                    new_faults.append(fault)

        self.fault_log.extend(new_faults)
        return new_faults

    # ------------------------------------------------------------------
    # Manual / forced injection
    # ------------------------------------------------------------------

    def force_inject(
        self,
        tick: int,
        sources: list[PowerSource],
        loads: list[PowerLoad],
        battery_grid: BatteryGrid,
    ) -> list[dict]:
        """Force at least one fault (used by the manual /grid/fault endpoint)."""
        if self.settings:
            saved_prob = self.settings.base_failure_chance
            self.settings.base_failure_chance = 100.0  # guarantees prob >= 1.0 under new math
            faults = self.inject(tick, sources, loads, battery_grid)
            self.settings.base_failure_chance = saved_prob
            return faults
        else:
            return self.inject(tick, sources, loads, battery_grid)

    def to_dict(self) -> dict:
        return {
            "fault_probability": self.settings.base_failure_chance if self.settings else 0.05,
            "total_faults": len(self.fault_log),
            "fault_log": self.fault_log,
        }
