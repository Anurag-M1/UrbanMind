import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.state_manager import state_manager
from services.emergency_manager import emergency_manager

logger = logging.getLogger("urbanmind.ws")
router = APIRouter(tags=["websocket"])

# Connection pool
active_connections: Set[WebSocket] = set()
_broadcast_lock = asyncio.Lock()


async def build_system_payload(intersections: list[Any], start_time: datetime) -> Dict[str, Any]:
    total_vehicles = sum(i.total_vehicles_processed for i in intersections)
    avg_wait = (
        sum(i.wait_time_avg for i in intersections) / len(intersections)
        if intersections
        else 0
    )
    active_emergencies = len(emergency_manager.get_active_vehicles())
    uptime = (datetime.utcnow() - start_time).total_seconds()

    baseline_wait = 45.0
    wait_reduction = max(0, (baseline_wait - avg_wait) / baseline_wait)
    emissions_pct = round(wait_reduction * 100 * 0.7, 1)

    stats = await state_manager.get_system_stats()
    vision_total = int(stats.get("vision_total_vehicles_detected", 0))
    redis_total = int(stats.get("total_vehicles_processed", 0))
    display_total = (
        vision_total
        if vision_total > 0
        else redis_total
        if redis_total > 0
        else total_vehicles
    )

    webster_interval = 10
    webster_recalcs = int(stats.get("webster_recalculations", 0))
    webster_countdown = webster_interval - (uptime % webster_interval)

    return {
        "total_vehicles": display_total,
        "vision_total_vehicles_detected": vision_total,
        "network_avg_wait": round(avg_wait),
        "webster_countdown": round(webster_countdown),
        "active_emergencies": active_emergencies,
        "emissions_saved_pct": round(emissions_pct),
        "uptime_seconds": round(uptime, 0),
        "webster_recalculations": webster_recalcs,
        "last_vision_update": stats.get("last_vision_update", ""),
        "last_detection_count": int(stats.get("last_detection_count", 0)),
        "live_vision_status": stats.get("live_vision_status", "Offline"),
        "last_siren_detected_at": stats.get("last_siren_detected_at", ""),
        "last_siren_vehicle_type": stats.get("last_siren_vehicle_type", ""),
        "siren_detection_confidence": int(float(stats.get("siren_detection_confidence", 0) or 0)),
        "siren_detection_status": stats.get("siren_detection_status", "Scanning"),
    }


async def broadcast(message: Dict[str, Any]) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    if not active_connections:
        return

    dead: Set[WebSocket] = set()
    payload = json.dumps(message, default=str)

    for ws in active_connections.copy():
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)

    for ws in dead:
        active_connections.discard(ws)


async def tick_loop() -> None:
    """Broadcast full state every 500ms to all WebSocket clients."""
    start_time = datetime.utcnow()

    while True:
        try:
            if active_connections:
                intersections = await state_manager.get_all_intersections()
                system_payload = await build_system_payload(intersections, start_time)

                message = {
                    "type": "tick",
                    "timestamp": datetime.utcnow().isoformat(),
                    "intersections": [
                        i.model_dump(mode="json") for i in intersections
                    ],
                    "system": system_payload,
                }

                await broadcast(message)

                # Update uptime in Redis
                await state_manager.update_system_stats(
                    uptime_seconds=system_payload["uptime_seconds"]
                )

        except Exception as e:
            logger.error("WebSocket tick error: %s", e)

        await asyncio.sleep(0.5)


@router.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time dashboard updates."""
    connection_start = datetime.utcnow()
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(
        "WebSocket connected. Active connections: %d", len(active_connections)
    )

    try:
        # Send initial state
        intersections = await state_manager.get_all_intersections()
        active_vehicles = emergency_manager.get_active_vehicles()
        system_payload = await build_system_payload(intersections, connection_start)

        init_message = {
            "type": "init",
            "intersections": [i.model_dump(mode="json") for i in intersections],
            "emergencies": [v.model_dump(mode="json") for v in active_vehicles],
            "system": system_payload,
        }
        await websocket.send_text(json.dumps(init_message, default=str))

        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Handle ping/pong or client messages
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_text(
                        json.dumps({"type": "keepalive"})
                    )
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("WebSocket error: %s", e)
    finally:
        active_connections.discard(websocket)
        logger.info(
            "WebSocket disconnected. Active connections: %d",
            len(active_connections),
        )
