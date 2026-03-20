"""Emergency API for vehicle registration, GPS updates, and demo simulation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.emergency import (
    EmergencyEventListResponse,
    EmergencyRegisterRequest,
    EmergencyStatus,
    EmergencyStatusResponse,
    EmergencyVehicleResponse,
    GPSUpdateRequest,
)
from models.intersection import OperationStatusResponse
from services.emergency_manager import emergency_manager

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.post("/register", response_model=EmergencyVehicleResponse)
async def register(payload: EmergencyRegisterRequest) -> EmergencyVehicleResponse:
    """Register a new active emergency vehicle."""

    try:
        vehicle = await emergency_manager.register_vehicle(payload.vehicle_id, payload.type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return EmergencyVehicleResponse(data=vehicle)


@router.post("/gps-update", response_model=EmergencyVehicleResponse)
async def gps_update(payload: GPSUpdateRequest) -> EmergencyVehicleResponse:
    """Update vehicle GPS data and refresh its active corridor."""

    try:
        vehicle = await emergency_manager.update_gps(
            payload.vehicle_id,
            payload.lat,
            payload.lng,
            payload.speed,
            payload.heading,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EmergencyVehicleResponse(data=vehicle)


@router.post("/deactivate/{vehicle_id}", response_model=OperationStatusResponse)
async def deactivate(vehicle_id: str) -> OperationStatusResponse:
    """Deactivate an emergency vehicle and release its corridor."""

    try:
        await emergency_manager.deactivate_vehicle(vehicle_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OperationStatusResponse(status="ok", message="Vehicle deactivated", resource_id=vehicle_id)


@router.get("/active", response_model=EmergencyStatusResponse)
async def active() -> EmergencyStatusResponse:
    """Return active vehicles and the currently reserved corridor."""

    vehicles = emergency_manager.list_active_vehicles()
    corridor = sorted({intersection_id for vehicle in vehicles for intersection_id in vehicle.corridor_intersections})
    return EmergencyStatusResponse(
        data=EmergencyStatus(
            active_vehicles=vehicles,
            active_corridor=corridor,
            total_preempted=len(corridor),
            conflicts=len([event for event in emergency_manager.recent_events(50) if event.event_type == "conflict"]),
        )
    )


@router.post("/simulate", response_model=EmergencyVehicleResponse)
async def simulate() -> EmergencyVehicleResponse:
    """Launch the built-in demo emergency route."""

    vehicle = await emergency_manager.simulate_emergency("ambulance")
    return EmergencyVehicleResponse(data=vehicle)


@router.get("/history", response_model=EmergencyEventListResponse)
async def history() -> EmergencyEventListResponse:
    """Return recent emergency events."""

    return EmergencyEventListResponse(data=emergency_manager.recent_events(20))
