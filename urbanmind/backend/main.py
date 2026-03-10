from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import emergency, intersections, signals, telemetry
from backend.services.corridor_manager import CorridorManager
from backend.services.gps_tracker import EmergencyGpsTracker
from backend.services.redis_state import RedisStateStore

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - optional dependency
    mqtt = None


LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s"
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format=LOG_FORMAT)
LOGGER = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    """Parses allowed CORS origins from environment variables."""

    raw = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _intersection_locations() -> dict[str, tuple[float, float]]:
    """Parses intersection locations from environment variables.

    Args:
        None.

    Returns:
        Mapping of intersection ids to coordinates.
    """

    raw = os.getenv("INTERSECTION_LOCATIONS_JSON", "{}")
    data = json.loads(raw)
    return {
        str(intersection_id): (float(value["lat"]), float(value["lon"]))
        for intersection_id, value in data.items()
    }


def _on_mqtt_message(client: Any, userdata: Any, message: Any) -> None:
    """Persists MQTT telemetry into Redis and history storage.

    Args:
        client: MQTT client instance.
        userdata: Attached app state.
        message: MQTT message.

    Returns:
        None.
    """

    try:
        payload = json.loads(message.payload.decode("utf-8"))
        intersection_id = payload["intersection_id"]
        userdata.redis_state.set_intersection_state(intersection_id, payload)
        userdata.redis_state.append_history(intersection_id, payload)
    except Exception as exc:  # pragma: no cover - network dependent
        LOGGER.warning("failed to handle MQTT message: %s", exc)


def _create_mqtt_client(app: FastAPI) -> Any:
    """Creates and starts the backend MQTT subscriber.

    Args:
        app: FastAPI application instance.

    Returns:
        MQTT client or None.
    """

    if mqtt is None:
        LOGGER.warning("paho-mqtt unavailable; MQTT subscription disabled")
        return None
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.user_data_set(app.state)
    client.on_message = _on_mqtt_message
    host = os.getenv("MQTT_HOST", "127.0.0.1")
    port = int(os.getenv("MQTT_PORT", "1883"))
    try:
        client.connect(host, port, 30)
        client.subscribe("urbanmind/intersection/+/state", qos=1)
        client.loop_start()
        return client
    except Exception as exc:  # pragma: no cover - depends on infra
        LOGGER.warning("failed to connect MQTT subscriber: %s", exc)
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes shared services for the FastAPI app.

    Args:
        app: FastAPI application instance.

    Returns:
        Async generator for lifespan handling.
    """

    app.state.redis_state = RedisStateStore()
    app.state.corridor_manager = CorridorManager(_intersection_locations())
    app.state.gps_tracker = EmergencyGpsTracker()
    app.state.mqtt_client = _create_mqtt_client(app)
    yield
    if app.state.mqtt_client is not None:
        app.state.mqtt_client.loop_stop()
        app.state.mqtt_client.disconnect()


app = FastAPI(title="UrbanMind Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(intersections.router)
app.include_router(signals.router)
app.include_router(emergency.router)
app.include_router(telemetry.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Returns a health status response.

    Args:
        None.

    Returns:
        Health status dictionary.
    """

    return {"status": "ok"}


def main() -> None:
    """Runs the backend server with uvicorn when executed directly.

    Args:
        None.

    Returns:
        None.
    """

    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
