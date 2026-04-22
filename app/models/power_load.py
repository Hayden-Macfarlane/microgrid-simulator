"""
power_load.py — Abstract base class for all power-consuming loads
and concrete implementations (LifeSupport, Heater, Lighting).
"""

from abc import ABC, abstractmethod
import random
import uuid


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
    def update(self, tick: int) -> None:
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
# Concrete implementations
# ---------------------------------------------------------------------------

class LifeSupport(PowerLoad):
    """
    Critical system — constant draw with minor fluctuations.
    Always marked essential.
    """

    def __init__(
        self,
        name: str = "Life Support",
        max_draw: float = 20.0,
    ) -> None:
        super().__init__(name, max_draw, is_essential=True)
        self._base_draw = max_draw

    def update(self, tick: int) -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        # Slight variation ±5 %
        self.max_draw = self._base_draw * random.uniform(0.95, 1.05)
        self.current_draw = self.max_draw


class Heater(PowerLoad):
    """
    Heating system — draw increases during the simulated 'night' cycle
    (colder periods). Non-essential; can be shed in emergencies.
    """

    DAY_TICKS = 1440

    def __init__(
        self,
        name: str = "Habitat Heater",
        max_draw: float = 15.0,
    ) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int) -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        time_of_day = tick % self.DAY_TICKS
        # Higher draw at night (tick 0 = midnight)
        import math
        night_factor = 1.0 + 0.5 * max(0.0, -math.sin(math.pi * time_of_day / self.DAY_TICKS) + 0.3)
        self.max_draw = self._base_draw * night_factor
        self.current_draw = self.max_draw


class Lighting(PowerLoad):
    """
    Lighting system — non-essential, constant draw when active.
    """

    def __init__(
        self,
        name: str = "Interior Lighting",
        max_draw: float = 5.0,
    ) -> None:
        super().__init__(name, max_draw, is_essential=False)
        self._base_draw = max_draw

    def update(self, tick: int) -> None:
        if self.repair_ticks_remaining > 0:
            self.repair_ticks_remaining -= 1
            if self.repair_ticks_remaining == 0:
                self.is_active = True
                
        if not self.is_active or self.is_manually_disabled:
            self.current_draw = 0.0
            return
        self.max_draw = self._base_draw
        self.current_draw = self.max_draw
