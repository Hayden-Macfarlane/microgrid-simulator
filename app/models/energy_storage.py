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
        id: str = None
    ) -> None:
        self.id = id if id else str(uuid.uuid4().hex)[:8]
        self.name = name
        self._base_max_capacity = max_capacity       # kWh
        self.current_charge = current_charge         # kWh
        self.max_charge_rate = max_charge_rate       # kW limit per module
        self.base_max_discharge_rate = max_discharge_rate # kW limit per module
        
        self.health_percentage = 100.0
        self.temperature = 20.0
        self.is_online = True
        self._last_draw_ratio = 0.0
        
        # Target SOC Limits
        self.target_soc_min: float = 20.0
        self.target_soc_max: float = 80.0
        
        self.internal_temperature: float = 20.0
        
    @property
    def current_soc(self) -> float:
        """Calculates (current_charge / max_capacity) * 100."""
        if self.max_capacity <= 0:
            return 0.0
        return (self.current_charge / self.max_capacity) * 100.0
        
    @property
    def max_capacity(self) -> float:
        """Usable capacity is limited by health."""
        return self._base_max_capacity * (self.health_percentage / 100.0)
        
    @property
    def max_discharge_rate(self) -> float:
        """Thermal throttling cuts discharge rate in half if hot."""
        if self.internal_temperature > 50.0:
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
            "temperature": round(self.internal_temperature, 1),
            "internal_temperature": round(self.internal_temperature, 1),
            "effective_max_capacity": round(self.max_capacity, 4),
            "user_soc_min": self.target_soc_min,
            "user_soc_max": self.target_soc_max,
            "is_online": self.is_online,
        }

    def tick(self, env_temp: float = 20.0, heating_active: bool = False, cooling_active: bool = False) -> None:
        """Update module physics for one tick."""
        try:
            # 1. Ambient Drift
            self.internal_temperature += (env_temp - self.internal_temperature) * 0.05
            
            # 2. HVAC Intervention
            if heating_active and self.internal_temperature < 15.0:
                self.internal_temperature = min(20.0, self.internal_temperature + 2.0)
            elif cooling_active and self.internal_temperature > 25.0:
                self.internal_temperature = max(20.0, self.internal_temperature - 2.0)

            # 3. Usage Heat
            if getattr(self, '_last_draw_ratio', 0.0) > 0.8:
                self.internal_temperature += 2.0 * self._last_draw_ratio
        except Exception:
            # Fallback to safe internal temperature if math fails
            self.internal_temperature = 20.0
        
        # 4. Cap charge tightly to updated bounds
        self.current_charge = min(self.current_charge, self.max_capacity)
        self._last_draw_ratio = 0.0

    def apply_discharge_wear(self, amount_kwh: float, base_deg_rate: float, reserve_unlocked: bool) -> None:
        """Degrade health based on energy discharged (1% loss per 100 full cycles)."""
        if self._base_max_capacity > 0:
            # Base logic: 100 full cycles = 1% health loss when rate is 1.0
            wear = (amount_kwh / self._base_max_capacity) * (base_deg_rate / 100.0)
            
            # Deep Discharge Penalty: 3x wear if using the last 10% reserve
            charge_pct = self.current_charge / self.max_capacity
            if reserve_unlocked and charge_pct < 0.10:
                wear *= 3.0
            
            self.health_percentage = max(0.0, self.health_percentage - wear)


class BatteryGrid:
    """Manages an array of BatteryModules."""

    def __init__(self, modules: Optional[List[BatteryModule]] = None) -> None:
        self.modules: List[BatteryModule] = modules if modules is not None else []
        self.reserve_unlocked: bool = False
        self._last_deg_rate: float = 0.05  # Default fallback logic before first tick

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
        """Distribute charge proportionally amongst online modules below target_soc_max."""
        eligible = [m for m in self.modules if m.is_online and m.current_soc < m.target_soc_max]
        if not eligible or amount_kw <= 0:
            return 0.0

        total_available_charge = sum(m.max_charge_rate for m in eligible)
        if total_available_charge == 0:
            return 0.0

        charge_ratio = min(1.0, amount_kw / total_available_charge)
        total_charged = 0.0

        for m in eligible:
            # Add proportional share limited by module's rate
            add = m.max_charge_rate * charge_ratio
            
            # Double check we don't overfill here (though controller usually manages bulk)
            headroom = m.max_capacity - m.current_charge
            actual = min(add, headroom)
            actual = max(0.0, actual)
            
            m.current_charge += actual
            total_charged += actual
            
        return total_charged

    def discharge(self, amount_kw: float) -> float:
        """Distribute discharge proportionally amongst online modules above target_soc_min."""
        eligible = [m for m in self.modules if m.is_online and m.current_soc > m.target_soc_min]
        if not eligible or amount_kw <= 0:
            return 0.0

        total_available_discharge = sum(m.max_discharge_rate for m in eligible)
        if total_available_discharge == 0:
            return 0.0

        discharge_ratio = amount_kw / total_available_discharge
        total_discharged = 0.0

        for m in eligible:
            draw = m.max_discharge_rate * discharge_ratio
            
            # Ensure we don't draw more than module's current available energy
            avail = max(0.0, m.current_charge - (m.max_capacity * (m.target_soc_min / 100.0)))
            # Also limit by inverter capacity
            actual = min(draw, m.max_discharge_rate, avail)
            actual = max(0.0, actual)
            
            # Apply degradation
            m.apply_discharge_wear(actual, getattr(self, '_last_deg_rate', 0.05), self.reserve_unlocked)
            
            m.current_charge -= actual
            m._last_draw_ratio = actual / (m.base_max_discharge_rate if m.base_max_discharge_rate > 0 else 1.0)
            
            total_discharged += actual
            
        return total_discharged

    def tick(self, degradation_rate: float = 0.05, env_temp: float = 20.0, heating_active: bool = False, cooling_active: bool = False) -> None:
        """Update physical properties per tick."""
        self._last_deg_rate = degradation_rate
        for m in self.modules:
            m.tick(env_temp=env_temp, heating_active=heating_active, cooling_active=cooling_active)

    def to_dict(self) -> dict:
        total_cap = self.max_capacity
        charge_pct = 0.0
        # If reserve locked, useable 10s as 0
        if total_cap > 0:
            charge_pct = (self.current_charge / total_cap) * 100.0

        return {
            "modules": [m.to_dict() for m in self.modules],
            "reserve_unlocked": self.reserve_unlocked,
            "max_capacity_kwh": round(total_cap, 4),
            "current_charge_kwh": round(self.current_charge, 4),
            "charge_pct": round(charge_pct, 2),
            "max_charge_rate_kw": round(self.max_charge_rate, 4),
            "max_discharge_rate_kw": round(self.max_discharge_rate, 4),
        }
