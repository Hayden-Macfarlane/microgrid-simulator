"""
environment_engine.py — Centralized engine to manage weather and day/night cycles.
"""
from dataclasses import dataclass
import random
import math

@dataclass
class EnvironmentState:
    time_of_day: float = 12.0         # 0.0 to 24.0 (Start at Noon)
    solar_efficiency: float = 1.0     # 0.0 to 1.0 (Peaks at noon)
    wind_efficiency: float = 1.0      # Scalar
    heater_demand: float = 1.0        # Scalar (Peaks at night)
    life_support_demand: float = 1.0  # Scalar
    day_activity_demand: float = 1.0  # Scalar (Peaks during day)
    night_activity_demand: float = 1.0 # Scalar (Peaks during night)
    current_event: str = "Clear Skies"
    event_ticks_remaining: int = 0
    current_temperature: float = 20.0
    ambient_temperature: float = 20.0

class EnvironmentEngine:
    """Manages global environmental factors like time of day and weather events."""

    HOURS_PER_TICK = 0.5  # Add 0.5 hours (30 mins) every tick to accelerate cycle

    def __init__(self):
        self.state = EnvironmentState()

    def tick(self, current_tick: int) -> EnvironmentState:
        # Update Time of Day
        if current_tick > 0:  # Don't increment on very first tick
            self.state.time_of_day = (self.state.time_of_day + self.HOURS_PER_TICK) % 24.0

        t = self.state.time_of_day

        # Base Modifiers from Day/Night cycle
        # solar_factor: Peak at 12, zero at 6 and 18
        solar_factor = max(0.0, math.sin(math.pi * (t - 6.0) / 12.0))
        self.state.solar_efficiency = solar_factor

        # day_activity: Peaks around noon, tapers off
        self.state.day_activity_demand = 0.5 + 0.5 * max(0.0, math.sin(math.pi * (t - 6.0) / 12.0))

        # night_activity / heater: Peaks at midnight, lowest at noon
        night_factor = 1.0 + 0.5 * max(0.0, -math.sin(math.pi * (t - 6.0) / 12.0) + 0.3)
        self.state.heater_demand = night_factor
        self.state.night_activity_demand = night_factor

        # current_temperature: Peak 35 at 12:00, Bottom -15 at 00:00
        # Formula: 10 + 25 * sin(...) -> sin(-pi/2)=-1 @ 0h -> -15, sin(pi/2)=1 @ 12h -> 35
        temp = 10.0 + 25.0 * math.sin(math.pi * (t - 6.0) / 12.0)
        self.state.current_temperature = temp
        self.state.ambient_temperature = temp

        # Reset defaults that might be overridden by events
        self.state.wind_efficiency = 1.0
        self.state.life_support_demand = 1.0

        # Weather Event Logic
        if self.state.event_ticks_remaining > 0:
            self.state.event_ticks_remaining -= 1
        else:
            self.state.current_event = "Clear Skies"

        # Chance to spawn a new event if currently clear
        if self.state.current_event == "Clear Skies":
            if random.random() < 0.005:  # ~0.5% chance per tick to start an event
                events = ["Dust Storm", "Cold Snap", "High Winds"]
                self.state.current_event = random.choice(events)
                # Durations: 8 ticks (4h) to 96 ticks (48h)
                self.state.event_ticks_remaining = random.randint(8, 96)

        # Apply Weather Overrides
        if self.state.current_event == "Dust Storm":
            self.state.solar_efficiency = 0.1
            self.state.wind_efficiency = 1.5
            self.state.heater_demand *= 1.2
        elif self.state.current_event == "Cold Snap":
            self.state.heater_demand *= 3.0
            self.state.life_support_demand *= 3.0
        elif self.state.current_event == "High Winds":
            self.state.wind_efficiency = 2.0

        return self.state
