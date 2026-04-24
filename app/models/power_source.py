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

    def __init__(self, name: str, max_output: float, id: str = None) -> None:
        self.id = id if id else str(uuid.uuid4().hex)[:8]
        self.name = name
        self.max_output = max_output       # kW
        self.current_output: float = 0.0   # kW (set each tick)
        self.is_operational: bool = True
        self.repair_ticks_remaining: int = 0
        self.is_manually_disabled: bool = False
        self.inertia_constant: float = 0.0  # s-scale (e.g., 5.0 for rotating mass)

    @abstractmethod
    def update(self, tick: int, env: 'EnvironmentState') -> None:
        """Recalculate current_output for the given simulation tick."""

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__,
            "max_output_kw": round(float(self.max_output), 4),
            "current_output_kw": round(float(self.current_output), 4),
            "is_operational": self.is_operational,
            "repair_ticks_remaining": self.repair_ticks_remaining,
            "is_manually_disabled": self.is_manually_disabled,
        }
        if hasattr(self, 'dust_coverage'):
            d["dust_coverage"] = round(self.dust_coverage, 4)
        if hasattr(self, 'is_cleaning'):
            d["is_cleaning"] = self.is_cleaning
        d["inertia_constant"] = self.inertia_constant
        return d


# ---------------------------------------------------------------------------
# Concrete implementations
# ---------------------------------------------------------------------------

class SolarPanel(PowerSource):
    """
    Output follows a sinusoidal day/night cycle.
    Peak output at tick 720 (noon in a 1440-tick / 24-hour day).
    """

    DAY_TICKS = 1440  # minutes in 24 hours

    def __init__(self, name: str = "Solar Array", max_output: float = 50.0, id: str = None) -> None:
        super().__init__(name, max_output, id=id)
        self.dust_coverage: float = 0.0  # 0.0 to 100.0
        self.is_cleaning: bool = False
        self.inertia_constant: float = 0.0 # Digital inverter

    def degrade_solar_efficiency(self, is_storm: bool = False) -> None:
        """Increases dust coverage. Base rate 0.01% per tick, 10x during storm."""
        rate = 0.1 if is_storm else 0.01
        self.dust_coverage = min(100.0, self.dust_coverage + rate)

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_operational = True
            
        if not self.is_operational or self.is_manually_disabled:
            self.current_output = 0.0
            return
            
        # Accumulate dust and calculate degradation
        is_storm = (env.current_event == "Dust Storm")
        self.degrade_solar_efficiency(is_storm=is_storm)
        dust_factor = (1.0 - (self.dust_coverage / 100.0))
            
        # Add slight random cloud cover (±10%)
        noise = random.uniform(0.90, 1.10)
        self.current_output = self.max_output * env.solar_efficiency * noise * dust_factor


class WindTurbine(PowerSource):
    """
    Output is stochastic — wind speed modelled with random walk drift.
    """

    def __init__(self, name: str = "Wind Turbine", max_output: float = 30.0, id: str = None) -> None:
        super().__init__(name, max_output, id=id)
        self._wind_factor: float = 0.5  # 0.0 → 1.0
        self.inertia_constant: float = 5.0 # Rotating mass

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

    def __init__(self, name: str = "RTG Unit", max_output: float = 10.0, id: str = None) -> None:
        super().__init__(name, max_output, id=id)

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


class KineticFlywheel(PowerSource):
    """
    High-inertia mechanical stabilizer.
    Provides massive stability but consumes power to stay at speed.
    """
    def __init__(self, name: str = "Kinetic Flywheel", max_output: float = 0.0, id: str = None) -> None:
        super().__init__(name, max_output, id=id)
        self.inertia_constant = 15.0
        self.parasitic_draw = 5.0 # kW

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_operational = True
        
        if not self.is_operational or self.is_manually_disabled:
            self.current_output = 0.0
            return
            
        # Kinetic flywheel consumes power to maintain momentum
        self.current_output = -self.parasitic_draw
