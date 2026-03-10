from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(tags=["telemetry"])


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    """Streams current and delta state updates to dashboard clients.

    Args:
        websocket: WebSocket connection.

    Returns:
        None.
    """

    await websocket.accept()
    app = websocket.app
    last_seen: dict[str, str] = {}
    try:
        await websocket.send_json(
            {
                "type": "snapshot",
                "intersections": app.state.redis_state.get_all_intersection_states(),
                "emergencies": app.state.corridor_manager.get_active_corridors(),
            }
        )
        for intersection in app.state.redis_state.get_all_intersection_states():
            last_seen[intersection["intersection_id"]] = intersection.get("timestamp", "")
        while True:
            await asyncio.sleep(2)
            all_states = app.state.redis_state.get_all_intersection_states()
            changed = []
            for intersection in all_states:
                current_timestamp = intersection.get("timestamp", "")
                if last_seen.get(intersection["intersection_id"]) != current_timestamp:
                    changed.append(intersection)
                    last_seen[intersection["intersection_id"]] = current_timestamp
            await websocket.send_json(
                {
                    "type": "delta",
                    "intersections": changed,
                    "emergencies": app.state.corridor_manager.get_active_corridors(),
                }
            )
    except WebSocketDisconnect:
        return
