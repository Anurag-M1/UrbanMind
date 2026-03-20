"""Intersection CRUD endpoints used by seed scripts and operational tooling."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.intersection import (
    IntersectionCreateRequest,
    IntersectionListResponse,
    IntersectionResponse,
    IntersectionState,
    OperationStatusResponse,
)
from services import state_manager

router = APIRouter(prefix="/intersections", tags=["intersections"])


@router.post("/", response_model=IntersectionResponse, status_code=201)
async def create_intersection(payload: IntersectionCreateRequest) -> IntersectionResponse:
    """Create or replace an intersection state."""

    state = IntersectionState(
        id=payload.id,
        name=payload.name,
        lat=payload.lat,
        lng=payload.lng,
        ew_green=payload.ew_green,
        ew_phase_seconds=payload.ew_phase_seconds,
        ew_green_duration=payload.ew_green_duration,
        ns_green_duration=payload.ns_green_duration,
        density_ew=payload.density_ew,
        density_ns=payload.density_ns,
        queue_ew=payload.queue_ew,
        queue_ns=payload.queue_ns,
        wait_time_avg=payload.wait_time_avg,
        override=payload.override,
        fault=payload.fault,
    )
    await state_manager.set_intersection(state)
    return IntersectionResponse(data=state)


@router.get("/", response_model=IntersectionListResponse)
async def list_intersections() -> IntersectionListResponse:
    """Return all created intersections."""

    return IntersectionListResponse(data=await state_manager.get_all_intersections())


@router.get("/{intersection_id}", response_model=IntersectionResponse)
async def read_intersection(intersection_id: str) -> IntersectionResponse:
    """Return one intersection state by ID."""

    state = await state_manager.get_intersection(intersection_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Intersection {intersection_id} not found")
    return IntersectionResponse(data=state)


@router.delete("/{intersection_id}", response_model=OperationStatusResponse)
async def delete_intersection(intersection_id: str) -> OperationStatusResponse:
    """Delete an intersection from Redis."""

    if not await state_manager.delete_intersection(intersection_id):
        raise HTTPException(status_code=404, detail=f"Intersection {intersection_id} not found")
    return OperationStatusResponse(status="ok", message="Intersection deleted", resource_id=intersection_id)
