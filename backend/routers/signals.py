"""Signal control API for live state, density updates, and manual overrides."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.intersection import (
    DensityUpdate,
    DensityUpdateResponse,
    IntersectionListResponse,
    IntersectionResponse,
    IntersectionStats,
    IntersectionStatsResponse,
    ManualSignalCommandRequest,
    OperationStatusResponse,
    SignalCommand,
    SignalCommandResponse,
)
from services import state_manager
from services.cv_engine import apply_density_measurement
from services.signal_controller import publish_signal_command
from services.webster import calculate_optimal_timings

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/intersections", response_model=IntersectionListResponse)
async def list_intersections() -> IntersectionListResponse:
    """Return every current intersection state."""

    return IntersectionListResponse(data=await state_manager.get_all_intersections())


@router.get("/intersection/{intersection_id}", response_model=IntersectionResponse)
async def get_intersection(intersection_id: str) -> IntersectionResponse:
    """Return a single current intersection state."""

    state = await state_manager.get_intersection(intersection_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Intersection {intersection_id} not found")
    return IntersectionResponse(data=state)


@router.post("/intersection/{intersection_id}/command", response_model=SignalCommandResponse)
async def manual_command(intersection_id: str, payload: ManualSignalCommandRequest) -> SignalCommandResponse:
    """Apply a manual signal command and publish it to the controller."""

    state = await state_manager.get_intersection(intersection_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Intersection {intersection_id} not found")

    state.override = True
    state.ew_green_duration = payload.ew_green_duration
    state.ns_green_duration = payload.ns_green_duration
    await state_manager.set_intersection(state)

    command = SignalCommand(
        intersection_id=intersection_id,
        ew_green_duration=payload.ew_green_duration,
        ns_green_duration=payload.ns_green_duration,
        immediate=payload.immediate,
    )
    await publish_signal_command(command)
    return SignalCommandResponse(data=command)


@router.post("/intersection/{intersection_id}/reset", response_model=OperationStatusResponse)
async def reset_intersection(intersection_id: str) -> OperationStatusResponse:
    """Release an intersection back to adaptive Webster control."""

    state = await state_manager.get_intersection(intersection_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Intersection {intersection_id} not found")

    timings = calculate_optimal_timings(state.density_ew, state.density_ns)
    state.override = False
    state.ew_green_duration = timings["ew_green"]
    state.ns_green_duration = timings["ns_green"]
    await state_manager.set_intersection(state)
    await publish_signal_command(
        SignalCommand(
            intersection_id=intersection_id,
            ew_green_duration=timings["ew_green"],
            ns_green_duration=timings["ns_green"],
            immediate=False,
        )
    )
    return OperationStatusResponse(
        status="ok",
        message="Intersection returned to adaptive mode",
        resource_id=intersection_id,
    )


@router.post("/density", response_model=DensityUpdateResponse)
async def receive_density(update: DensityUpdate) -> DensityUpdateResponse:
    """Persist a CV density update and derived analytics values."""

    if await state_manager.get_intersection(update.intersection_id) is None:
        raise HTTPException(status_code=404, detail=f"Intersection {update.intersection_id} not found")
    await apply_density_measurement(update)
    return DensityUpdateResponse(data=update)


@router.get("/stats", response_model=IntersectionStatsResponse)
async def network_stats() -> IntersectionStatsResponse:
    """Return live aggregate signal-network statistics."""

    intersections = await state_manager.get_all_intersections()
    stats = IntersectionStats(
        total_intersections=len(intersections),
        online_count=sum(1 for item in intersections if not item.fault),
        faulted_count=sum(1 for item in intersections if item.fault),
        overridden_count=sum(1 for item in intersections if item.override),
        network_avg_wait_time=await state_manager.get_network_average_wait(),
        total_vehicles_detected=sum(item.density_ew + item.density_ns for item in intersections),
    )
    return IntersectionStatsResponse(data=stats)
