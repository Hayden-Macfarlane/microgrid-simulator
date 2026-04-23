"""
power_load.py — Abstract base class for all power-consuming loads
and concrete implementations.
"""

from abc import ABC, abstractmethod
import random
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.environment_engine import EnvironmentState

class PowerLoad(ABC):
    """Base class for any device that consumes power on the microgrid."""

    def __init__(
        self,
        name: str,
        max_draw: float,
        is_essential: bool = False,
    ) -> None:
        self.id = str(uuid.uuid4().hex)[:8]
        self.name = name
        self.max_draw = max_draw          # kW (nominal maximum)
        self.current_draw: float = 0.0    # kW (dynamically scaled)
        self.is_essential = is_essential   # If True, cannot be shed
        self.is_active: bool = True        # Controller may deactivate non-essentials
        self.repair_ticks_remaining: int = 0
        self.is_manually_disabled: bool = False

    @abstractmethod
    def update(self, tick: int, env: 'EnvironmentState') -> None:
        """Recalculate power_draw for the given simulation tick."""
        ...

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.__class__.__name__,
            "max_draw_kw": round(float(self.max_draw), 4),
            "current_draw_kw": round(float(self.current_draw), 4),
            "is_essential": self.is_essential,
            "is_active": self.is_active,
            "repair_ticks_remaining": self.repair_ticks_remaining,
            "is_manually_disabled": self.is_manually_disabled,
        }


# ---------------------------------------------------------------------------
# Essential loads
# ---------------------------------------------------------------------------

class LifeSupport(PowerLoad):
    """Critical system — scaled by life_support_demand from environment."""
    def __init__(self, name: str = "Life Support", max_draw: float = 20.0) -> None:
        super().__init__(name, max_draw, is_essential=True)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        
        self.max_draw = self._base_draw * env.life_support_demand * random.uniform(0.95, 1.05)
        self.current_draw = self.max_draw


class Heater(PowerLoad):
    """Heating system — scales primarily with heater_demand (night and weather)."""
    def __init__(self, name: str = "Habitat Heater", max_draw: float = 15.0) -> None:
        super().__init__(name, max_draw, is_essential=True)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
            
        self.max_draw = self._base_draw * env.heater_demand
        self.current_draw = self.max_draw


# ---------------------------------------------------------------------------
# Non-essential loads
# ---------------------------------------------------------------------------

class Lighting(PowerLoad):
    """Scales with night_activity_demand."""
    def __init__(self, name: str = "Interior Lighting", max_draw: float = 5.0) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        self.max_draw = self._base_draw * env.night_activity_demand
        self.current_draw = self.max_draw


class ExternalComms(PowerLoad):
    """Constant non-essential load."""
    def __init__(self, name: str = "External Communications", max_draw: float = 8.0) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        self.max_draw = self._base_draw
        self.current_draw = self.max_draw


class WaterFiltration(PowerLoad):
    """Constant non-essential load with minor noise."""
    def __init__(self, name: str = "Water Filtration", max_draw: float = 12.0) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        self.max_draw = self._base_draw * random.uniform(0.9, 1.1)
        self.current_draw = self.max_draw


class ScienceLab(PowerLoad):
    """Scales with day_activity_demand."""
    def __init__(self, name: str = "Science Lab", max_draw: float = 25.0) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        self.max_draw = self._base_draw * env.day_activity_demand
        self.current_draw = self.max_draw


class RoverBay(PowerLoad):
    """Scales with day_activity_demand."""
    def __init__(self, name: str = "Rover Charging Bay", max_draw: float = 40.0) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        self.max_draw = self._base_draw * env.day_activity_demand
        self.current_draw = self.max_draw


class Extractors(PowerLoad):
    """Scales with day_activity_demand."""
    def __init__(self, name: str = "Resource Extractors", max_draw: float = 55.0) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        self.max_draw = self._base_draw * env.day_activity_demand
        self.current_draw = self.max_draw
