"""
power_source.py — Abstract base class for all power generation sources
and concrete implementations (Solar, Wind, RTG).
"""

from abc import ABC, abstractmethod
import math
import random
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.environment_engine import EnvironmentState


class PowerSource(ABC):
    """Base class for any device that generates power on the microgrid."""

    def __init__(self, name: str, max_output: float) -> None:
        self.id = str(uuid.uuid4().hex)[:8]
        self.name = name
        self.max_output = max_output       # kW
        self.current_output: float = 0.0   # kW (set each tick)
        self.is_operational: bool = True
        self.repair_ticks_remaining: int = 0
        self.is_manually_disabled: bool = False

    @abstractmethod
    def update(self, tick: int, env: 'EnvironmentState') -> None:
        """Recalculate current_output for the given simulation tick."""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__,
            "max_output_kw": round(float(self.max_output), 4),
            "current_output_kw": round(float(self.current_output), 4),
            "is_operational": self.is_operational,
            "repair_ticks_remaining": self.repair_ticks_remaining,
            "is_manually_disabled": self.is_manually_disabled,
        }


# ---------------------------------------------------------------------------
# Concrete implementations
# ---------------------------------------------------------------------------

class SolarPanel(PowerSource):
    """
    Output follows a sinusoidal day/night cycle.
    Peak output at tick 720 (noon in a 1440-tick / 24-hour day).
    """

    DAY_TICKS = 1440  # minutes in 24 hours

    def __init__(self, name: str = "Solar Array", max_output: float = 50.0) -> None:
        super().__init__(name, max_output)

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_operational = True
            
        if not self.is_operational or self.is_manually_disabled:
            self.current_output = 0.0
            return
            
        # Add slight random cloud cover (±10%)
        noise = random.uniform(0.90, 1.10)
        self.current_output = self.max_output * env.solar_efficiency * noise


class WindTurbine(PowerSource):
    """
    Output is stochastic — wind speed modelled with random walk drift.
    """

    def __init__(self, name: str = "Wind Turbine", max_output: float = 30.0) -> None:
        super().__init__(name, max_output)
        self._wind_factor: float = 0.5  # 0.0 → 1.0

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_operational = True
                
        # High Winds physical fault logic (0.5% chance per tick to suffer fault)
        if env.current_event == "High Winds":
            if random.random() < 0.005 and self.is_operational:
                self.is_operational = False
                self.repair_ticks_remaining = random.randint(60, 120)

        if not self.is_operational or self.is_manually_disabled:
            self.current_output = 0.0
            return
            
        # Random walk bounded between 0 and 1
        self._wind_factor += random.uniform(-0.05, 0.05)
        self._wind_factor = max(0.0, min(1.0, self._wind_factor))
        self.current_output = self.max_output * self._wind_factor * env.wind_efficiency


class RTG(PowerSource):
    """
    Radioisotope Thermoelectric Generator — near-constant output with
    very slow decay over long timescales.
    """

    HALF_LIFE_TICKS = 525_600 * 10  # ~10 years in minutes

    def __init__(self, name: str = "RTG Unit", max_output: float = 10.0) -> None:
        super().__init__(name, max_output)

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_operational = True
                
        if not self.is_operational or self.is_manually_disabled:
            self.current_output = 0.0
            return
        # Exponential decay (barely noticeable over short sims)
        decay = 0.5 ** (tick / self.HALF_LIFE_TICKS)
        self.current_output = self.max_output * decay
