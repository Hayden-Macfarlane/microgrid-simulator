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
        id: str = None
    ) -> None:
        self.id = id if id else str(uuid.uuid4().hex)[:8]
        self.name = name
        self.max_draw = max_draw          # kW (nominal maximum)
        self.current_draw: float = 0.0    # kW (dynamically scaled)
        self.is_essential = is_essential   # If True, cannot be shed
        self.is_active: bool = True        # Controller may deactivate non-essentials
        self.repair_ticks_remaining: int = 0
        self.is_manually_disabled: bool = False
        self.is_grid_throttled: bool = False

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
            "is_grid_throttled": self.is_grid_throttled,
        }


# ---------------------------------------------------------------------------
# Essential loads
# ---------------------------------------------------------------------------

class LifeSupport(PowerLoad):
    """Critical system — scaled by life_support_demand from environment."""
    def __init__(self, name: str = "Life Support", max_draw: float = 20.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=True, id=id)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        
        self.max_draw = self._base_draw * env.life_support_demand
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)


class Heater(PowerLoad):
    """Heating system — scales primarily with heater_demand (night and weather)."""
    def __init__(self, name: str = "Habitat Heater", max_draw: float = 15.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=True, id=id)
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
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)


# ---------------------------------------------------------------------------
# Non-essential loads
# ---------------------------------------------------------------------------

class Lighting(PowerLoad):
    """Scales with night_activity_demand."""
    def __init__(self, name: str = "Interior Lighting", max_draw: float = 5.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
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
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)


class ExternalComms(PowerLoad):
    """Constant non-essential load."""
    def __init__(self, name: str = "External Communications", max_draw: float = 8.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
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
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)


class WaterFiltration(PowerLoad):
    """Constant non-essential load with minor noise."""
    def __init__(self, name: str = "Water Filtration", max_draw: float = 12.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
        self._base_draw = max_draw
        self._was_active = True
        self.inrush_ticks_remaining = 0
        self.inrush_multiplier = 3.5

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self._was_active = False
            self.current_draw = 0.0
            return
            
        self.max_draw = self._base_draw
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)
        
        if self.is_active and not self._was_active:
            self.inrush_ticks_remaining = 2
        
        self._was_active = self.is_active
        
        if self.inrush_ticks_remaining > 0:
            self.current_draw *= self.inrush_multiplier
            self.inrush_ticks_remaining -= 1


class ScienceLab(PowerLoad):
    """Scales with day_activity_demand."""
    def __init__(self, name: str = "Science Lab", max_draw: float = 25.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
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
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)


class RoverBay(PowerLoad):
    """Scales with day_activity_demand."""
    def __init__(self, name: str = "Rover Charging Bay", max_draw: float = 40.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
        self._base_draw = max_draw
        self._was_active = True
        self.inrush_ticks_remaining = 0
        self.inrush_multiplier = 4.0

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self._was_active = False
            self.current_draw = 0.0
            return
            
        self.max_draw = self._base_draw * env.day_activity_demand
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)
        
        if self.is_active and not self._was_active:
            self.inrush_ticks_remaining = 2
        
        self._was_active = self.is_active
        
        if self.inrush_ticks_remaining > 0:
            self.current_draw *= self.inrush_multiplier
            self.inrush_ticks_remaining -= 1


class Extractors(PowerLoad):
    """Scales with day_activity_demand."""
    def __init__(self, name: str = "Resource Extractors", max_draw: float = 55.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
        self._base_draw = max_draw
        self._was_active = True
        self.inrush_ticks_remaining = 0
        self.inrush_multiplier = 3.5

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self._was_active = False
            self.current_draw = 0.0
            return
            
        self.max_draw = self._base_draw * env.day_activity_demand
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)
        
        if self.is_active and not self._was_active:
            self.inrush_ticks_remaining = 2
        
        self._was_active = self.is_active
        
        if self.inrush_ticks_remaining > 0:
            self.current_draw *= self.inrush_multiplier
            self.inrush_ticks_remaining -= 1


class ActiveHeating(PowerLoad):
    """HVAC unit for warming batteries and habitats."""
    def __init__(self, name: str = "Active Heating", max_draw: float = 25.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
            
        # HVAC turns on if temperature is low
        if env.current_temperature < 15.0:
            self.current_draw = self._base_draw * random.uniform(0.95, 1.05)
        else:
            self.current_draw = 0.0


class ActiveCooling(PowerLoad):
    """HVAC unit for cooling batteries and habitats."""
    def __init__(self, name: str = "Active Cooling", max_draw: float = 25.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=False, id=id)
        self._base_draw = max_draw

    def update(self, tick: int, env: 'EnvironmentState') -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
            
        # HVAC turns on if temperature is high
        if env.current_temperature > 25.0:
            self.current_draw = self._base_draw * random.uniform(0.95, 1.05)
        else:
            self.current_draw = 0.0


class StaticLoad(PowerLoad):
    """Generic concrete implementation of PowerLoad for constant-ish loads."""
    def __init__(self, name: str, max_draw: float, is_essential: bool = False, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential, id)
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
        self.current_draw = self.max_draw * random.uniform(0.95, 1.05)


class EngineeringFabricationHub(PowerLoad):
    """
    Standby power for diagnostic computers, fabrication tools, and environmental control.
    """
    def __init__(self, name: str = "Engineering & Maintenance Hub", max_draw: float = 10.0, id: str = None) -> None:
        super().__init__(name, max_draw, is_essential=True, id=id)
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
        self.current_draw = self.max_draw * random.uniform(0.98, 1.02) # Very stable load

