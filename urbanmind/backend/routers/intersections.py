from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query, Request


router = APIRouter(prefix="/intersections", tags=["intersections"])


@router.get("")
def list_intersections(request: Request) -> list[dict]:
    """Returns all known intersection states.

    Args:
        request: FastAPI request.

    Returns:
        List of intersection states.
    """

    return request.app.state.redis_state.get_all_intersection_states()


@router.get("/{intersection_id}")
def get_intersection(intersection_id: str, request: Request) -> dict:
    """Returns one intersection state.

    Args:
        intersection_id: Intersection identifier.
        request: FastAPI request.

    Returns:
        State dictionary.
    """

    state = request.app.state.redis_state.get_intersection_state(intersection_id)
    if state is None:
        raise HTTPException(status_code=404, detail="intersection_not_found")
    return state


@router.get("/{intersection_id}/history")
def get_intersection_history(
    intersection_id: str,
    request: Request,
    minutes: int = Query(default=60, ge=1, le=60),
) -> list[dict]:
    """Returns recent state history for one intersection.

    Args:
        intersection_id: Intersection identifier.
        request: FastAPI request.
        minutes: Number of minutes to return.

    Returns:
        History entries.
    """

    return request.app.state.redis_state.get_history(intersection_id, minutes)


@router.post("/{intersection_id}/state")
def ingest_intersection_state(
    intersection_id: str,
    request: Request,
    payload: dict = Body(...),
) -> dict:
    """Stores an externally posted state snapshot for simulation or testing.

    Args:
        intersection_id: Intersection identifier.
        request: FastAPI request.

    Returns:
        Ingestion acknowledgement.
    """

    request.app.state.redis_state.set_intersection_state(intersection_id, payload)
    request.app.state.redis_state.append_history(intersection_id, payload)
    return {"status": "accepted", "intersection_id": intersection_id}
