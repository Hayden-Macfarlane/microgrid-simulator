"""
settings.py — Configuration parameters for the simulation engine.
"""

from dataclasses import dataclass

@dataclass
class SimulationSettings:
    battery_degradation_rate: float = 0.1   # Percentage (0.1%)
    base_failure_chance: float = 1.0        # Percentage (1.0%)
    min_repair_ticks: int = 5
    max_repair_ticks: int = 15
    shed_threshold: float = 0.10
    throttle_threshold: float = 0.20
    user_soc_min: float = 20.0
    user_soc_max: float = 80.0

    def to_dict(self) -> dict:
        return {
            "battery_degradation_rate": self.battery_degradation_rate,
            "base_failure_chance": self.base_failure_chance,
            "min_repair_ticks": self.min_repair_ticks,
            "max_repair_ticks": self.max_repair_ticks,
            "shed_threshold": self.shed_threshold,
            "throttle_threshold": self.throttle_threshold,
            "user_soc_min": self.user_soc_min,
            "user_soc_max": self.user_soc_max,
        }
