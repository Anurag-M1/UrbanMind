"""MQTT publishing, Modbus control, and inbound signal-event handling for UrbanMind."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Awaitable, Callable

import paho.mqtt.client as mqtt_client

from config import settings
from models.emergency import EmergencyOverride, GPSUpdateRequest
from models.intersection import SignalCommand
from models.signal import SignalHardwareStatus
from utils import failsafe

logger = logging.getLogger("urbanmind.signal_controller")

MqttHandler = Callable[[str, dict[str, object]], Awaitable[None]]

_mqtt_client: mqtt_client.Client | None = None
_mqtt_connected = False
_event_loop: asyncio.AbstractEventLoop | None = None
_subscriptions_registered = False
_handlers: dict[str, list[MqttHandler]] = {}


def _on_connect(
    client: mqtt_client.Client,
    _userdata: object,
    _flags: mqtt_client.ConnectFlags,
    reason_code: mqtt_client.ReasonCode,
    _properties: mqtt_client.Properties | None = None,
) -> None:
    """Subscribe to all controller-relevant topics when MQTT connects."""

    global _mqtt_connected, _subscriptions_registered
    _mqtt_connected = reason_code == mqtt_client.ReasonCode(mqtt_client.CONNACK_ACCEPTED)
    if not _mqtt_connected:
        logger.error("MQTT connection rejected: %s", reason_code)
        return

    subscriptions = [
        ("urbanmind/intersection/+/ack", 1),
        ("urbanmind/intersection/+/fault", 1),
        ("urbanmind/vehicle/gps", 1),
        ("urbanmind/sensor/siren", 1),
    ]
    for topic, qos in subscriptions:
        client.subscribe(topic, qos=qos)
    _subscriptions_registered = True
    logger.info("MQTT connected and subscriptions registered")


def _on_disconnect(
    _client: mqtt_client.Client,
    _userdata: object,
    _flags: mqtt_client.DisconnectFlags,
    reason_code: mqtt_client.ReasonCode,
    _properties: mqtt_client.Properties | None = None,
) -> None:
    """Track MQTT connectivity state."""

    global _mqtt_connected
    _mqtt_connected = False
    logger.warning("MQTT disconnected: %s", reason_code)


def _dispatch_async(topic: str, payload: dict[str, object]) -> None:
    """Schedule async topic handlers onto the API event loop from the MQTT thread."""

    if _event_loop is None:
        return
    for pattern, handlers in _handlers.items():
        if mqtt_client.topic_matches_sub(pattern, topic):
            for handler in handlers:
                asyncio.run_coroutine_threadsafe(handler(topic, payload), _event_loop)


def _on_message(_client: mqtt_client.Client, _userdata: object, message: mqtt_client.MQTTMessage) -> None:
    """Decode inbound JSON messages and hand them to async handlers."""

    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except json.JSONDecodeError:
        logger.error("Invalid JSON received on %s", message.topic)
        return
    except Exception as exc:
        logger.error("Failed to parse MQTT message on %s: %s", message.topic, exc)
        return

    _dispatch_async(message.topic, payload)


def get_mqtt_client() -> mqtt_client.Client:
    """Create or return the shared Paho MQTT client."""

    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = mqtt_client.Client(
            client_id="urbanmind-api",
            protocol=mqtt_client.MQTTv5,
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        )
        _mqtt_client.on_connect = _on_connect
        _mqtt_client.on_disconnect = _on_disconnect
        _mqtt_client.on_message = _on_message
    return _mqtt_client


def register_topic_handler(pattern: str, handler: MqttHandler) -> None:
    """Register an async callback for MQTT messages matching a subscription."""

    _handlers.setdefault(pattern, []).append(handler)


async def connect_mqtt() -> bool:
    """Connect to MQTT with three attempts and 1-second incremental backoff."""

    global _event_loop
    _event_loop = asyncio.get_running_loop()
    client = get_mqtt_client()

    for attempt in range(1, 4):
        try:
            client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
            client.loop_start()
            await asyncio.sleep(1)
            if _mqtt_connected:
                _register_default_handlers()
                return True
        except Exception as exc:
            logger.error("MQTT connect attempt %d failed: %s", attempt, exc)
        await asyncio.sleep(1)
    return False


async def disconnect_mqtt() -> None:
    """Disconnect the MQTT client gracefully."""

    global _mqtt_client, _mqtt_connected
    if _mqtt_client is None:
        return
    _mqtt_client.loop_stop()
    _mqtt_client.disconnect()
    _mqtt_client = None
    _mqtt_connected = False


def is_mqtt_connected() -> bool:
    """Return whether the MQTT client is connected."""

    return _mqtt_connected


async def _publish(topic: str, payload: dict[str, object], qos: int = 1) -> bool:
    """Publish JSON to MQTT with three attempts and 1-second backoff."""

    client = get_mqtt_client()
    for attempt in range(1, 4):
        try:
            result = client.publish(topic, json.dumps(payload), qos=qos)
            if result.rc == mqtt_client.MQTT_ERR_SUCCESS:
                return True
            logger.warning("Publish rc=%s for %s on attempt %d", result.rc, topic, attempt)
        except Exception as exc:
            logger.error("Failed publishing %s on attempt %d: %s", topic, attempt, exc)
        await asyncio.sleep(1)
    return False


async def publish_signal_command(command: SignalCommand) -> bool:
    """Publish a normal adaptive or manual signal command."""

    payload = command.model_dump(mode="json")
    payload["timestamp"] = command.timestamp.isoformat()
    topic = f"urbanmind/intersection/{command.intersection_id}/command"
    return await _publish(topic, payload, qos=1)


async def publish_emergency_override(override: EmergencyOverride) -> bool:
    """Publish an emergency override command with high delivery guarantees."""

    payload = override.model_dump(mode="json")
    payload["timestamp"] = override.timestamp.isoformat()
    topic = f"urbanmind/intersection/{override.intersection_id}/emergency"
    return await _publish(topic, payload, qos=2)


async def publish_system_alert(message: str, level: str, data: dict[str, object] | None = None) -> bool:
    """Publish a system broadcast message used by simulators and dashboards."""

    payload = {
        "level": level,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    return await _publish("urbanmind/system/broadcast", payload, qos=1)


class SignalControllerAdapter:
    """Modbus adapter with MQTT fallback for signal hardware communication."""

    def __init__(self) -> None:
        self._client: object | None = None
        self._connected = False

    async def connect(self) -> bool:
        """Attempt to initialize the Modbus client."""

        try:
            from pymodbus.client import AsyncModbusTcpClient

            self._client = AsyncModbusTcpClient("signal-controller", port=502)
            self._connected = await self._client.connect()
        except Exception as exc:
            logger.warning("Modbus unavailable, using MQTT fallback: %s", exc)
            self._connected = False
        return self._connected

    async def write_phase(self, intersection_id: str, ew_green: bool) -> bool:
        """Write the current phase using Modbus when available, or MQTT otherwise."""

        if self._connected and self._client is not None:
            try:
                slave = int(intersection_id.split("_")[-1])
                result = await self._client.write_register(0, 1 if ew_green else 0, slave=slave)
                if not result.isError():
                    return True
            except Exception as exc:
                logger.error("Modbus write failed for %s: %s", intersection_id, exc)
                self._connected = False
                await failsafe.activate_failsafe(intersection_id)

        await publish_system_alert(
            message=f"MQTT fallback controlling {intersection_id}",
            level="warning",
            data={"intersection_id": intersection_id},
        )
        return await _publish(
            f"urbanmind/intersection/{intersection_id}/command",
            {
                "intersection_id": intersection_id,
                "ew_green": ew_green,
                "timestamp": datetime.utcnow().isoformat(),
            },
            qos=1,
        )

    async def read_status(self, intersection_id: str) -> SignalHardwareStatus | None:
        """Read controller status or return a synthetic MQTT-backed status."""

        if self._connected and self._client is not None:
            try:
                slave = int(intersection_id.split("_")[-1])
                result = await self._client.read_holding_registers(0, 2, slave=slave)
                if not result.isError():
                    return SignalHardwareStatus(
                        intersection_id=intersection_id,
                        connected=True,
                        protocol="modbus",
                    )
            except Exception as exc:
                logger.error("Modbus status read failed for %s: %s", intersection_id, exc)
                self._connected = False
                await failsafe.activate_failsafe(intersection_id)
                return None

        if _mqtt_connected:
            return SignalHardwareStatus(intersection_id=intersection_id, connected=True, protocol="mqtt")
        return None


signal_adapter = SignalControllerAdapter()


def _register_default_handlers() -> None:
    """Install default MQTT handlers once per process."""

    if getattr(_register_default_handlers, "_done", False):
        return

    register_topic_handler("urbanmind/intersection/+/fault", _handle_fault)
    register_topic_handler("urbanmind/intersection/+/ack", _handle_ack)
    register_topic_handler("urbanmind/vehicle/gps", _handle_vehicle_gps)
    register_topic_handler("urbanmind/sensor/siren", _handle_siren)
    setattr(_register_default_handlers, "_done", True)


async def _handle_fault(topic: str, payload: dict[str, object]) -> None:
    """Process fault events and move the intersection into failsafe mode."""

    from routers import ws

    intersection_id = str(payload.get("intersection_id") or topic.split("/")[2])
    await failsafe.activate_failsafe(intersection_id)
    await ws.broadcast_fault_event(intersection_id, str(payload.get("message", "Hardware fault")))


async def _handle_ack(topic: str, payload: dict[str, object]) -> None:
    """Handle controller acknowledgements by clearing transient fault state."""

    intersection_id = str(payload.get("intersection_id") or topic.split("/")[2])
    if await failsafe.is_failsafe_active(intersection_id):
        await failsafe.clear_failsafe(intersection_id)
    logger.info("Signal controller ACK received for %s", intersection_id)


async def _handle_vehicle_gps(_topic: str, payload: dict[str, object]) -> None:
    """Forward emergency GPS messages to the emergency manager."""

    from services.emergency_manager import emergency_manager

    try:
        update = GPSUpdateRequest.model_validate(payload)
    except Exception as exc:
        logger.error("Invalid GPS payload: %s", exc)
        return
    await emergency_manager.update_gps(
        update.vehicle_id,
        update.lat,
        update.lng,
        update.speed,
        update.heading,
    )


async def _handle_siren(_topic: str, payload: dict[str, object]) -> None:
    """Turn confident siren detections into emergency corridor activations."""

    from services.emergency_manager import emergency_manager

    confidence = float(payload.get("confidence", 0.0))
    nearest_intersection = payload.get("nearest_intersection")
    if confidence < 0.85 or nearest_intersection is None:
        return
    await emergency_manager.activate_siren_corridor(str(nearest_intersection))
