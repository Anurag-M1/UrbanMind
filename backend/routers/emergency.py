import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.emergency_manager import emergency_manager
from services.state_manager import state_manager

logger = logging.getLogger("urbanmind.router.emergency")
router = APIRouter(prefix="/api/v1/emergency", tags=["emergency"])

ws_broadcast = None


def set_ws_broadcast(fn):  # type: ignore
    global ws_broadcast
    ws_broadcast = fn


class SimulateRequest(BaseModel):
    vehicle_type: str  # "ambulance" | "fire" | "police"


class ManualGPSRequest(BaseModel):
    vehicle_id: str
    lat: float
    lng: float
    speed_kmh: float = 50.0
    heading: float = 0.0


@router.post("/simulate")
async def simulate_emergency(req: SimulateRequest):
    """Start an emergency vehicle simulation."""
    valid_types = {"ambulance", "fire", "police"}
    if req.vehicle_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid vehicle type. Must be one of: {', '.join(valid_types)}",
        )

    # Check if too many active
    active = emergency_manager.get_active_vehicles()
    if len(active) >= emergency_manager.MAX_ACTIVE:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {emergency_manager.MAX_ACTIVE} concurrent emergencies",
        )

    result = await emergency_manager.simulate_emergency(
        req.vehicle_type, state_manager, ws_broadcast
    )

    return result


@router.get("/active")
async def get_active_emergencies():
    """Get all active emergency vehicles and their corridor states."""
    vehicles = emergency_manager.get_active_vehicles()
    result = []
    for v in vehicles:
        corridor_states = []
        for int_id in v.corridor_intersections:
            state = await state_manager.get_intersection(int_id)
            if state:
                corridor_states.append(state.model_dump(mode="json"))
        result.append({
            "vehicle": v.model_dump(mode="json"),
            "corridor_states": corridor_states,
        })
    return {"active": result, "count": len(result)}


@router.post("/deactivate/{vehicle_id}")
async def deactivate_emergency(vehicle_id: str):
    """Manually deactivate an emergency vehicle."""
    success = await emergency_manager.deactivate_vehicle(
        vehicle_id, state_manager, ws_broadcast
    )
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found or already deactivated")
    return {"deactivated": True, "vehicle_id": vehicle_id}


@router.get("/history")
async def get_emergency_history():
    """Get emergency event history."""
    # Try Redis first, fall back to in-memory
    events = await state_manager.get_emergency_events(50)
    if not events:
        events = emergency_manager.get_event_history(50)
    return {
        "events": [e.model_dump(mode="json") for e in events],
        "count": len(events),
    }


@router.post("/manual-gps")
async def manual_gps_update(req: ManualGPSRequest):
    """Inject a manual GPS position for a vehicle (for real device integration)."""
    vehicle = emergency_manager.active_vehicles.get(req.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    vehicle.lat = req.lat
    vehicle.lng = req.lng
    vehicle.speed_kmh = req.speed_kmh
    vehicle.heading_degrees = req.heading

    if ws_broadcast:
        await ws_broadcast({
            "type": "vehicle_position",
            "vehicle_id": req.vehicle_id,
            "lat": req.lat,
            "lng": req.lng,
            "speed_kmh": req.speed_kmh,
            "heading": req.heading,
        })

    return {"updated": True, "vehicle_id": req.vehicle_id}
