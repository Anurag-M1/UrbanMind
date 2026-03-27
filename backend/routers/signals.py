import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.state_manager import state_manager

logger = logging.getLogger("urbanmind.router.signals")
router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


class SignalOverrideRequest(BaseModel):
    ew_green: Optional[bool] = None
    ew_green_duration: Optional[int] = None
    ns_green_duration: Optional[int] = None
    override: Optional[bool] = None
    override_reason: Optional[str] = None
    fault: Optional[bool] = None


@router.get("/")
async def get_all_signals():
    """Get all intersection signal states."""
    intersections = await state_manager.get_all_intersections()
    return {
        "intersections": [i.model_dump(mode="json") for i in intersections],
        "count": len(intersections),
    }


@router.get("/{intersection_id}")
async def get_signal(intersection_id: str):
    """Get a single intersection's state."""
    state = await state_manager.get_intersection(intersection_id)
    if not state:
        raise HTTPException(status_code=404, detail="Intersection not found")
    # Fetch wait history
    history = await state_manager.get_wait_history(intersection_id)
    state.wait_time_history = history[:60]
    return state.model_dump(mode="json")


@router.put("/{intersection_id}")
async def update_signal(intersection_id: str, req: SignalOverrideRequest):
    """Manually override signal state."""
    state = await state_manager.get_intersection(intersection_id)
    if not state:
        raise HTTPException(status_code=404, detail="Intersection not found")

    if req.ew_green is not None:
        state.ew_green = req.ew_green
    if req.ew_green_duration is not None:
        state.ew_green_duration = req.ew_green_duration
    if req.ns_green_duration is not None:
        state.ns_green_duration = req.ns_green_duration
    if req.override is not None:
        state.override = req.override
    if req.override_reason is not None:
        state.override_reason = req.override_reason
    if req.fault is not None:
        state.fault = req.fault

    await state_manager.set_intersection(state)

    return {"updated": True, "intersection": state.model_dump(mode="json")}


@router.post("/{intersection_id}/toggle")
async def toggle_signal(intersection_id: str):
    """Toggle the signal phase between EW and NS green."""
    state = await state_manager.get_intersection(intersection_id)
    if not state:
        raise HTTPException(status_code=404, detail="Intersection not found")

    state.ew_green = not state.ew_green
    state.ew_phase_seconds = 0.0
    await state_manager.set_intersection(state)

    return {
        "toggled": True,
        "ew_green": state.ew_green,
        "intersection_id": intersection_id,
    }
