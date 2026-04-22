"""
energy_storage.py — Advanced battery system modeling modules and the Grid.
"""

import uuid
from typing import List, Optional


class BatteryModule:
    """Represents a single modular battery unit."""

    def __init__(
        self,
        name: str,
        max_capacity: float = 100.0,
        current_charge: float = 50.0,
        max_charge_rate: float = 25.0,
        max_discharge_rate: float = 25.0,
    ) -> None:
        self.id = str(uuid.uuid4().hex)[:8]
        self.name = name
        self._base_max_capacity = max_capacity       # kWh
        self.current_charge = current_charge         # kWh
        self.max_charge_rate = max_charge_rate       # kW limit per module
        self.base_max_discharge_rate = max_discharge_rate # kW limit per module
        
        self.health_percentage = 100.0
        self.temperature = 20.0
        self.is_online = True
        self._last_draw_ratio = 0.0
        
    @property
    def max_capacity(self) -> float:
        """Usable capacity is limited by health."""
        return self._base_max_capacity * (self.health_percentage / 100.0)
        
    @property
    def max_discharge_rate(self) -> float:
        """Thermal throttling cuts discharge rate in half if hot."""
        if self.temperature > 50.0:
            return self.base_max_discharge_rate * 0.5
        return self.base_max_discharge_rate

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "max_capacity_kwh": round(self.max_capacity, 4),
            "current_charge_kwh": round(self.current_charge, 4),
            "max_charge_rate_kw": self.max_charge_rate,
            "max_discharge_rate_kw": round(self.max_discharge_rate, 4),
            "health_percentage": round(self.health_percentage, 1),
            "temperature": round(self.temperature, 1),
            "is_online": self.is_online,
        }

    def tick(self, base_deg_rate: float, reserve_unlocked: bool) -> None:
        """Update module physics for one tick."""
        # 1. Thermal dynamics
        if getattr(self, '_last_draw_ratio', 0.0) > 0.8:
            self.temperature += 2.0 * self._last_draw_ratio
        else:
            self.temperature = max(20.0, self.temperature - 0.5)
        self._last_draw_ratio = 0.0

        # 2. DoD Degradation (uses exact float from settings)
        if self.max_capacity > 0:
            charge_pct = self.current_charge / self.max_capacity
            if charge_pct < 0.20:
                actual_deg = base_deg_rate / 100.0
                # Accelerate if in emergency reserve
                if reserve_unlocked and charge_pct <= 0.10:
                    actual_deg *= 3.0
                self.health_percentage = max(0.0, self.health_percentage - actual_deg)

        # Cap charge tightly to updated bounds
        self.current_charge = min(self.current_charge, self.max_capacity)


class BatteryGrid:
    """Manages an array of BatteryModules."""

    def __init__(self, modules: Optional[List[BatteryModule]] = None) -> None:
        self.modules: List[BatteryModule] = modules if modules is not None else []
        self.reserve_unlocked: bool = False

    @property
    def current_charge(self) -> float:
        return sum(m.current_charge for m in self.modules if m.is_online)

    @property
    def max_capacity(self) -> float:
        return sum(m.max_capacity for m in self.modules if m.is_online)

    @property
    def max_discharge_rate(self) -> float:
        return sum(m.max_discharge_rate for m in self.modules if m.is_online)

    @property
    def max_charge_rate(self) -> float:
        return sum(m.max_charge_rate for m in self.modules if m.is_online)

    def charge(self, amount_kw: float) -> float:
        """Distribute charge proportionally amongst online modules."""
        online = [m for m in self.modules if m.is_online]
        if not online or amount_kw <= 0:
            return 0.0

        total_headroom = sum(m.max_capacity - m.current_charge for m in online)
        if total_headroom <= 0:
            return 0.0

        total_charged = 0.0
        remaining_to_charge = amount_kw

        for m in online:
            if remaining_to_charge <= 0:
                break
            headroom = m.max_capacity - m.current_charge
            if headroom <= 0:
                continue
            
            proportion = headroom / total_headroom
            target_amount = amount_kw * proportion
            
            actual = min(target_amount, m.max_charge_rate, headroom)
            actual = max(0.0, actual)
            m.current_charge += actual
            total_charged += actual
            remaining_to_charge -= actual
            
        return total_charged

    def discharge(self, amount_kw: float) -> float:
        """Distribute discharge proportionally amongst online modules."""
        online = [m for m in self.modules if m.is_online]
        if not online or amount_kw <= 0:
            return 0.0

        total_discharged = 0.0
        remaining_demand = amount_kw

        def get_available(m: BatteryModule) -> float:
            floor = 0.0 if self.reserve_unlocked else m.max_capacity * 0.10
            return max(0.0, m.current_charge - floor)

        total_available = sum(get_available(m) for m in online)
        if total_available <= 0:
            return 0.0

        for m in online:
            if remaining_demand <= 0:
                break
            avail = get_available(m)
            if avail <= 0:
                continue
            
            proportion = avail / total_available
            target_draw = amount_kw * proportion
            
            actual = min(target_draw, m.max_discharge_rate, avail)
            actual = max(0.0, actual)
            
            m.current_charge -= actual
            m._last_draw_ratio = actual / m.base_max_discharge_rate
            
            total_discharged += actual
            remaining_demand -= actual
            
        return total_discharged

    def tick(self, degradation_rate: float = 0.05) -> None:
        """Update physical properties (temp, degradation) per tick."""
        for m in self.modules:
            m.tick(degradation_rate, self.reserve_unlocked)

    def to_dict(self) -> dict:
        total_cap = self.max_capacity
        charge_pct = 0.0
        # If reserve locked, useable 10s as 0
        if total_cap > 0:
            floor = 0.0 if self.reserve_unlocked else 0.10 * total_cap
            useable = total_cap - floor
            avail = max(0.0, self.current_charge - floor)
            if useable > 0:
                charge_pct = (avail / useable) * 100.0

        return {
            "modules": [m.to_dict() for m in self.modules],
            "reserve_unlocked": self.reserve_unlocked,
            "max_capacity_kwh": round(total_cap, 4),
            "current_charge_kwh": round(self.current_charge, 4),
            "charge_pct": round(charge_pct, 2),
            "max_charge_rate_kw": round(self.max_charge_rate, 4),
            "max_discharge_rate_kw": round(self.max_discharge_rate, 4),
        }
