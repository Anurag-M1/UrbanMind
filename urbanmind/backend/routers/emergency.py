from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

from backend.models import EmergencyActivateRequest, EmergencyUpdateRequest
from backend.services.corridor_manager import CorridorVehicle


router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.post("/activate")
def activate_emergency(body: EmergencyActivateRequest, request: Request) -> dict:
    """Activates a new emergency corridor.

    Args:
        body: Emergency activation request.
        request: FastAPI request.

    Returns:
        Corridor activation response.
    """

    corridor_id = f"corridor-{body.vehicle_id}"
    vehicle = CorridorVehicle(
        vehicle_id=body.vehicle_id,
        vehicle_type=body.vehicle_type,
        gps_lat=body.gps_lat,
        gps_lon=body.gps_lon,
        route=body.route,
        corridor_id=corridor_id,
    )
    request.app.state.gps_tracker.upsert(body.vehicle_id, body.gps_lat, body.gps_lon)
    status = request.app.state.corridor_manager.activate(vehicle)
    client = request.app.state.mqtt_client
    if client is not None:
        for intersection_id in status.pre_empted_intersections:
            client.publish(
                f"urbanmind/intersection/{intersection_id}/command",
                json.dumps({"type": "emergency_activate", "vehicle_id": body.vehicle_id}),
                qos=1,
            )
    return {
        "corridor_id": corridor_id,
        "intersections_pre_empted": status.pre_empted_intersections,
    }


@router.post("/update/{vehicle_id}")
def update_emergency(vehicle_id: str, body: EmergencyUpdateRequest, request: Request) -> dict:
    """Updates an emergency vehicle position.

    Args:
        vehicle_id: Vehicle identifier.
        body: Position update request.
        request: FastAPI request.

    Returns:
        Updated corridor state.
    """

    if vehicle_id not in request.app.state.corridor_manager.active_vehicles:
        raise HTTPException(status_code=404, detail="vehicle_not_found")
    request.app.state.gps_tracker.upsert(vehicle_id, body.gps_lat, body.gps_lon)
    status = request.app.state.corridor_manager.update_position(vehicle_id, body.gps_lat, body.gps_lon)
    client = request.app.state.mqtt_client
    if client is not None:
        for intersection_id in status.pre_empted_intersections:
            client.publish(
                f"urbanmind/intersection/{intersection_id}/command",
                json.dumps({"type": "emergency_update", "vehicle_id": vehicle_id}),
                qos=1,
            )
    return status.to_dict()


@router.post("/deactivate/{vehicle_id}")
def deactivate_emergency(vehicle_id: str, request: Request) -> dict:
    """Deactivates an emergency corridor.

    Args:
        vehicle_id: Vehicle identifier.
        request: FastAPI request.

    Returns:
        Deactivation acknowledgement.
    """

    active_before = request.app.state.corridor_manager.get_active_corridors()
    affected = {
        intersection_id
        for corridor in active_before
        if corridor["vehicle_id"] == vehicle_id
        for intersection_id in corridor["pre_empted_intersections"]
    }
    request.app.state.corridor_manager.deactivate(vehicle_id)
    request.app.state.gps_tracker.remove(vehicle_id)
    client = request.app.state.mqtt_client
    if client is not None:
        for intersection_id in affected:
            client.publish(
                f"urbanmind/intersection/{intersection_id}/command",
                json.dumps({"type": "emergency_deactivate", "vehicle_id": vehicle_id}),
                qos=1,
            )
    return {"status": "deactivated", "vehicle_id": vehicle_id}


@router.get("/active")
def get_active_emergencies(request: Request) -> list[dict]:
    """Returns all active corridors.

    Args:
        request: FastAPI request.

    Returns:
        List of active corridor states.
    """

    return request.app.state.corridor_manager.get_active_corridors()
