from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

from backend.models import SignalOverrideRequest


router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/{intersection_id}/override")
def apply_override(intersection_id: str, body: SignalOverrideRequest, request: Request) -> dict:
    """Publishes a manual signal override command.

    Args:
        intersection_id: Intersection identifier.
        body: Override request body.
        request: FastAPI request.

    Returns:
        Command acknowledgement.
    """

    client = request.app.state.mqtt_client
    if client is None:
        raise HTTPException(status_code=503, detail="mqtt_unavailable")
    topic = f"urbanmind/intersection/{intersection_id}/command"
    payload = {
        "type": "manual_override",
        "phase": body.phase,
        "duration_seconds": body.duration_seconds,
        "reason": body.reason,
    }
    client.publish(topic, json.dumps(payload), qos=1)
    return {"status": "override_sent", "topic": topic, "payload": payload}


@router.delete("/{intersection_id}/override")
def cancel_override(intersection_id: str, request: Request) -> dict:
    """Cancels a manual signal override.

    Args:
        intersection_id: Intersection identifier.
        request: FastAPI request.

    Returns:
        Cancellation acknowledgement.
    """

    client = request.app.state.mqtt_client
    if client is None:
        raise HTTPException(status_code=503, detail="mqtt_unavailable")
    topic = f"urbanmind/intersection/{intersection_id}/command"
    payload = {"type": "cancel_override"}
    client.publish(topic, json.dumps(payload), qos=1)
    return {"status": "override_cancelled", "topic": topic}
