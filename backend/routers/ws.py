"""WebSocket broadcast hub for the UrbanMind operations dashboard."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services import state_manager
from services.emergency_manager import emergency_manager

logger = logging.getLogger("urbanmind.ws")

router = APIRouter()
_connections: set[WebSocket] = set()
_last_webster_recalc = datetime.utcnow().isoformat()


def set_last_webster_recalc(timestamp: str) -> None:
    """Update the timestamp embedded in periodic dashboard broadcasts."""

    global _last_webster_recalc
    _last_webster_recalc = timestamp


async def _safe_broadcast(message: dict[str, object]) -> None:
    """Send a message to every connected dashboard client."""

    if not _connections:
        return
    dead_connections: list[WebSocket] = []
    payload = json.dumps(message, default=str)
    for connection in _connections:
        try:
            await connection.send_text(payload)
        except Exception:
            dead_connections.append(connection)
    for connection in dead_connections:
        _connections.discard(connection)


async def broadcast_emergency_event(vehicle: dict[str, object], corridor: list[str]) -> None:
    """Push an emergency activation event immediately."""

    await _safe_broadcast(
        {
            "type": "emergency_activated",
            "vehicle": vehicle,
            "corridor": corridor,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


async def broadcast_fault_event(intersection_id: str, message: str) -> None:
    """Push a fault event immediately."""

    await _safe_broadcast(
        {
            "type": "fault",
            "intersection_id": intersection_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


async def broadcast_loop() -> None:
    """Broadcast complete dashboard state every 500ms."""

    while True:
        try:
            intersections = await state_manager.get_all_intersections()
            active_vehicles = emergency_manager.list_active_vehicles()
            total_vehicles = sum(item.density_ew + item.density_ns for item in intersections)
            avg_wait = await state_manager.get_network_average_wait()
            baseline_wait = 45.0
            emissions_saved = max(0.0, min(100.0, ((baseline_wait - avg_wait) / baseline_wait) * 100)) if baseline_wait else 0.0
            await _safe_broadcast(
                {
                    "type": "state_update",
                    "intersections": [item.model_dump(mode="json") for item in intersections],
                    "emergency_active": bool(active_vehicles),
                    "active_vehicles": [item.model_dump(mode="json") for item in active_vehicles],
                    "system_stats": {
                        "total_vehicles_detected": total_vehicles,
                        "avg_wait_time_network": round(avg_wait, 2),
                        "webster_last_recalc": _last_webster_recalc,
                        "emissions_saved_pct": round(emissions_saved, 2),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("WebSocket broadcast loop failed: %s", exc, exc_info=True)
        await asyncio.sleep(0.5)


@router.websocket("/ws/dashboard")
async def dashboard_socket(websocket: WebSocket) -> None:
    """Accept dashboard WebSocket connections and keep them alive."""

    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections.discard(websocket)
