"""
main.py — FastAPI application for the Microgrid Simulator.
Provides REST endpoints to inspect and advance the simulation.
"""

import asyncio
import logging
import traceback
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    SolarPanel, WindTurbine, RTG,
    LifeSupport, Heater, Lighting,
    ExternalComms, WaterFiltration, ScienceLab, RoverBay, Extractors,
    EngineeringFabricationHub,
    ActiveHeating, ActiveCooling, StaticLoad,
    BatteryGrid, BatteryModule, FaultInjector,
)
from app.models.settings import SimulationSettings
from app.grid_controller import GridController

# -----------------------------------------------------------------------
# Pydantic request schemas
# -----------------------------------------------------------------------

class AddSourceRequest(BaseModel):
    type: str          # "SolarPanel", "WindTurbine", "RTG"
    name: str
    max_output: float
    dust_coverage: Optional[float] = 0.0

class AddLoadRequest(BaseModel):
    type: str          # "LifeSupport", "Heater", "Lighting"
    name: str
    max_draw: float
    is_essential: bool = False

class AddBatteryModuleRequest(BaseModel):
    name: str
    max_capacity: float
    max_charge_rate: float
    max_discharge_rate: float

class SettingsUpdateRequest(BaseModel):
    battery_degradation_rate: float
    base_failure_chance: float
    min_repair_ticks: int
    max_repair_ticks: int
    shed_threshold: float
    throttle_threshold: float
    user_soc_min: float
    user_soc_min: float
    user_soc_max: float

class IdRequest(BaseModel):
    id: str

# -----------------------------------------------------------------------
# Bootstrap the simulation
# -----------------------------------------------------------------------

app = FastAPI(
    title="Microgrid Simulator",
    description="Modular microgrid simulation engine with fault injection.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state instances
sources = []
loads = []
battery_grid = None
settings = None
fault_injector = None
grid = None
backend_critical_fault = False

def reset_grid():
    global sources, loads, battery_grid, settings, fault_injector, grid, backend_critical_fault
    
    try:
        sources = [
            SolarPanel(id="s1", name="Solar Array Alpha", max_output=250.0),
            SolarPanel(id="s2", name="Solar Array Bravo", max_output=250.0),
            WindTurbine(id="w1", name="Wind Turbine Charlie", max_output=50.0),
            RTG(id="r1", name="RTG Delta", max_output=15.0),
        ]

        loads = [
            LifeSupport(id="l1", name="Life Support", max_draw=20.0),
            Heater(id="l2", name="Habitat Heater", max_draw=15.0),
            Lighting(id="l3", name="Interior Lighting", max_draw=5.0),
            ExternalComms(id="l4", name="External Communications", max_draw=8.0),
            WaterFiltration(id="l5", name="Water Filtration", max_draw=12.0),
            ScienceLab(id="l6", name="Science Lab", max_draw=25.0),
            RoverBay(id="l7", name="Rover Charging Bay", max_draw=40.0),
            Extractors(id="l8", name="Resource Extractors", max_draw=55.0),
            EngineeringFabricationHub(id="l9", name="Engineering & Maintenance Hub", max_draw=10.0),
            ActiveHeating(id="h1", name="Active Heating", max_draw=25.0),
            ActiveCooling(id="c1", name="Active Cooling", max_draw=25.0),
        ]

        battery_grid = BatteryGrid(modules=[
            BatteryModule(id="b1", name="Substation Alpha", max_capacity=1500.0, current_charge=800.0, max_charge_rate=100.0, max_discharge_rate=100.0),
            BatteryModule(id="b2", name="Substation Bravo", max_capacity=1500.0, current_charge=800.0, max_charge_rate=100.0, max_discharge_rate=100.0),
        ])

        settings = SimulationSettings()
        fault_injector = FaultInjector(settings=settings)

        grid = GridController(
            sources=sources,
            loads=loads,
            battery_grid=battery_grid,
            fault_injector=fault_injector,
            settings=settings,
        )
        
        backend_critical_fault = False
        print("Backend: Grid simulation initialized successfully.")
        
    except Exception as e:
        print("CRITICAL: Failed to initialize grid simulation!")
        traceback.print_exc()
        backend_critical_fault = True
        
        # Safe Fallback: Empty Grid
        sources = []
        loads = []
        battery_grid = BatteryGrid(modules=[])
        settings = SimulationSettings()
        fault_injector = FaultInjector(settings=settings)
        grid = GridController(
            sources=sources,
            loads=loads,
            battery_grid=battery_grid,
            fault_injector=fault_injector,
            settings=settings,
        )

reset_grid()

# -----------------------------------------------------------------------
# Auto-tick background task
# -----------------------------------------------------------------------

auto_tick_task: Optional[asyncio.Task] = None
auto_tick_running: bool = False

async def _auto_tick_loop():
    global auto_tick_running
    while auto_tick_running:
        grid.tick()
        await asyncio.sleep(1.0)

# -----------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Diagnostic endpoint to verify API is alive."""
    return {"status": "alive"}

@app.get("/grid/state", summary="Get current grid state")
def get_grid_state():
    """Return the full snapshot of the microgrid."""
    try:
        state = grid.get_state()
        state["backend_critical_fault"] = backend_critical_fault
        return state
    except Exception as e:
        print("ERROR: Serialization of grid state failed!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/grid/tick", summary="Advance simulation by 1 tick")
def advance_one_tick():
    """Advance the simulation by one tick (1 simulated minute)."""
    return grid.tick()


@app.post("/grid/tick/{n}", summary="Advance simulation by N ticks")
def advance_n_ticks(n: int):
    """Advance the simulation by *n* ticks."""
    if n < 1:
        return {"error": "n must be >= 1"}
    if n > 10_000:
        return {"error": "n must be <= 10,000 to avoid timeout"}
    return grid.tick_multiple(n)


@app.post("/grid/fault", summary="Manually trigger a fault")
def trigger_fault():
    """Force-inject at least one fault into the grid."""
    return grid.force_fault()

@app.post("/grid/restart", summary="Restart the grid simulation")
def restart_simulation():
    """Reset the grid to its default state."""
    reset_grid()
    return {"message": "Simulation reset success.", "state": grid.get_state()}


# -----------------------------------------------------------------------
# New: Add source / load
# -----------------------------------------------------------------------

SOURCE_CLASSES = {
    "SolarPanel": SolarPanel,
    "WindTurbine": WindTurbine,
    "RTG": RTG,
}

LOAD_CLASSES = {
    "LifeSupport": LifeSupport,
    "Heater": Heater,
    "Lighting": Lighting,
    "ExternalComms": ExternalComms,
    "WaterFiltration": WaterFiltration,
    "ScienceLab": ScienceLab,
    "RoverBay": RoverBay,
    "Extractors": Extractors,
    "EngineeringFabricationHub": EngineeringFabricationHub,
    "ActiveHeating": ActiveHeating,
    "ActiveCooling": ActiveCooling,
    "StaticLoad": StaticLoad,
}


@app.post("/grid/source", summary="Add a new power source")
def add_source(req: AddSourceRequest):
    """Dynamically add a power source to the running simulation."""
    cls = SOURCE_CLASSES.get(req.type)
    if cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source type '{req.type}'. Choose from: {list(SOURCE_CLASSES.keys())}",
        )
    source = cls(name=req.name, max_output=req.max_output)
    return grid.add_source(source)


@app.post("/grid/load", summary="Add a new power load")
def add_load(req: AddLoadRequest):
    """Dynamically add a power load to the running simulation."""
    cls = LOAD_CLASSES.get(req.type)
    if cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown load type '{req.type}'. Choose from: {list(LOAD_CLASSES.keys())}",
        )
    load = cls(name=req.name, max_draw=req.max_draw)
    # Override is_essential for types that aren't LifeSupport
    if req.type != "LifeSupport":
        load.is_essential = req.is_essential
    return grid.add_load(load)


@app.post("/grid/settings", summary="Update simulation settings")
def update_settings(req: SettingsUpdateRequest):
    """Update realistic parameters for faults and failure events."""
    settings.battery_degradation_rate = req.battery_degradation_rate
    settings.base_failure_chance = req.base_failure_chance
    settings.min_repair_ticks = req.min_repair_ticks
    settings.max_repair_ticks = req.max_repair_ticks
    settings.shed_threshold = req.shed_threshold
    settings.throttle_threshold = req.throttle_threshold
    settings.user_soc_min = req.user_soc_min
    settings.user_soc_max = req.user_soc_max
    return {"message": "Settings updated", "settings": settings.to_dict()}

@app.post("/grid/source/{source_id}/toggle", summary="Toggle manual override for a source")
def toggle_source(source_id: str):
    for s in grid.sources:
        if s.id == source_id:
            s.is_manually_disabled = not s.is_manually_disabled
            return {"message": "Source toggled", "is_manually_disabled": s.is_manually_disabled}
    raise HTTPException(status_code=404, detail="Source not found")


@app.post("/grid/load/{load_id}/toggle", summary="Toggle manual override for a load")
def toggle_load(load_id: str):
    for l in grid.loads:
        if l.id == load_id:
            l.is_manually_disabled = not l.is_manually_disabled
            return {"message": "Load toggled", "is_manually_disabled": l.is_manually_disabled}
    raise HTTPException(status_code=404, detail="Load not found")


@app.post("/grid/battery/module", summary="Add a new battery module")
def add_battery_module(req: AddBatteryModuleRequest):
    """Dynamically add a battery module to the grid."""
    module = BatteryModule(
        name=req.name,
        max_capacity=req.max_capacity,
        current_charge=0.0,
        max_charge_rate=req.max_charge_rate,
        max_discharge_rate=req.max_discharge_rate,
    )
    grid.battery_grid.modules.append(module)
    return module.to_dict()


@app.post("/grid/battery/toggle-reserve", summary="Toggle emergency reserve lock")
def toggle_battery_reserve():
    grid.battery_grid.reserve_unlocked = not grid.battery_grid.reserve_unlocked
    return {"message": "Reserve toggled", "reserve_unlocked": grid.battery_grid.reserve_unlocked}


@app.post("/grid/battery/module/{module_id}/toggle", summary="Toggle a battery module ON/OFF")
def toggle_battery_module(module_id: str):
    for m in grid.battery_grid.modules:
        if m.id == module_id:
            m.is_online = not m.is_online
            return {"message": "Module toggled", "is_online": m.is_online}
    raise HTTPException(status_code=404, detail="Module not found")


# -----------------------------------------------------------------------
# Auto-tick
# -----------------------------------------------------------------------

@app.post("/grid/auto-tick", summary="Toggle auto-tick (1 tick / second)")
async def toggle_auto_tick():
    """Start or stop the auto-tick background loop."""
    global auto_tick_task, auto_tick_running

    if auto_tick_running:
        auto_tick_running = False
        if auto_tick_task:
            auto_tick_task.cancel()
            auto_tick_task = None
        return {"auto_tick": False, "message": "Auto-tick stopped."}
    else:
        auto_tick_running = True
        auto_tick_task = asyncio.create_task(_auto_tick_loop())
        return {"auto_tick": True, "message": "Auto-tick started (1 tick/sec)."}


@app.get("/grid/auto-tick/status", summary="Check auto-tick status")
def auto_tick_status():
    return {"auto_tick": auto_tick_running}


# -----------------------------------------------------------------------
# Phase 2 Maintenance Endpoints
# -----------------------------------------------------------------------

@app.post("/grid/battery/repair", summary="Submit repair request for a damaged battery")
def repair_battery(req: IdRequest):
    """Marks a battery for repair and calculates its initial energy debt."""
    module = next((m for m in grid.battery_grid.modules if m.id == req.id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Battery module not found.")
    
    if module.is_destroyed:
        raise HTTPException(status_code=400, detail="Destroyed modules cannot be repaired. Use Scrap instead.")
    
    if module.health_percentage >= 100.0:
        return {"message": "Battery is already at 100% health."}

    # Energy Debt: 5 kWh for every 1% of missing health
    module.energy_debt = (100.0 - module.health_percentage) * 5.0
    module.is_repairing = True
    module.is_scrapping = False
    return {"message": f"Repair request submitted for {module.name}. Energy Debt: {module.energy_debt} kWh."}


@app.post("/grid/battery/scrap", summary="Scrap a destroyed battery")
def scrap_battery(req: IdRequest):
    """Marks a destroyed battery for decommissioning/scrapping."""
    module = next((m for m in grid.battery_grid.modules if m.id == req.id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Battery module not found.")
    
    if not module.is_destroyed:
        raise HTTPException(status_code=400, detail="Only destroyed modules can be scrapped.")

    module.is_scrapping = True
    module.is_repairing = False
    module.scrap_progress = 0
    return {"message": f"Scrap operation started for {module.name}. 50 ticks remaining."}


@app.post("/grid/solar/clean", summary="Schedule panel cleaning")
def clean_solar(req: IdRequest):
    """Marks a solar array for cleaning."""
    source = next((s for s in grid.sources if s.id == req.id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Solar source not found.")
    
    if not isinstance(source, SolarPanel):
        raise HTTPException(status_code=400, detail="Only solar panels can be cleaned.")

    source.is_cleaning = True
    return {"message": f"Cleaning scheduled for {source.name}."}
