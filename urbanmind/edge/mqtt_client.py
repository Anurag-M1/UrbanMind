from __future__ import annotations

import json
import os
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.config import EdgeConfig, configure_logging, load_config

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - optional dependency
    mqtt = None


LOGGER = configure_logging(__name__)


class EdgeMqttPublisher:
    """Publishes edge state snapshots to an MQTT broker."""

    def __init__(self, config: EdgeConfig) -> None:
        """Initializes the MQTT publisher.

        Args:
            config: Edge runtime configuration.

        Returns:
            None.
        """

        self.config = config
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) if mqtt is not None else None
        self.connected = False
        self.backoff_seconds = 1
        if self.client is not None:
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        """Handles MQTT connect events.

        Args:
            client: MQTT client.
            userdata: Arbitrary user data.
            flags: Broker flags.
            reason_code: MQTT reason code.
            properties: MQTT properties.

        Returns:
            None.
        """

        self.connected = True
        self.backoff_seconds = 1
        LOGGER.info("connected to MQTT broker")

    def _on_disconnect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        """Handles MQTT disconnect events.

        Args:
            client: MQTT client.
            userdata: Arbitrary user data.
            flags: Broker flags.
            reason_code: MQTT reason code.
            properties: MQTT properties.

        Returns:
            None.
        """

        self.connected = False
        LOGGER.warning("MQTT disconnected with code=%s", reason_code)

    def connect(self) -> None:
        """Connects to the MQTT broker with exponential backoff.

        Args:
            None.

        Returns:
            None.
        """

        if self.client is None:
            LOGGER.warning("paho-mqtt not installed; publisher disabled")
            return
        while not self.connected:
            try:
                self.client.connect(self.config.mqtt_host, self.config.mqtt_port, keepalive=30)
                self.client.loop_start()
                time.sleep(0.5)
            except Exception as exc:  # pragma: no cover - network dependent
                LOGGER.warning("MQTT connect failed: %s", exc)
                time.sleep(self.backoff_seconds)
                self.backoff_seconds = min(60, self.backoff_seconds * 2)

    def _device_health(self, inference_ms: float) -> dict[str, float]:
        """Builds a device health snapshot.

        Args:
            inference_ms: Most recent inference latency.

        Returns:
            Device health metrics.
        """

        load_avg = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {
            "cpu_pct": round(min(100.0, load_avg * 100), 2),
            "mem_pct": round(mem_kb / 1_000_000, 2),
            "inference_ms": round(inference_ms, 2),
        }

    def publish_state(self, payload: dict[str, Any]) -> bool:
        """Publishes one state payload to the configured MQTT topic.

        Args:
            payload: State payload to publish.

        Returns:
            True when publish was acknowledged locally.
        """

        if self.client is None:
            LOGGER.warning("publish skipped because MQTT dependency is missing")
            return False
        topic = f"urbanmind/intersection/{self.config.intersection_id}/state"
        try:
            if not self.connected:
                self.connect()
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            return result.rc == 0
        except Exception as exc:  # pragma: no cover - network dependent
            LOGGER.warning("publish failed: %s", exc)
            self.connected = False
            self.connect()
            return False

    def build_payload(
        self,
        lane_densities: dict[str, Any],
        current_signal_plan: dict[str, Any],
        emergency_active: bool,
        corridor_status: dict[str, Any] | None,
        inference_ms: float,
    ) -> dict[str, Any]:
        """Builds the canonical MQTT state payload.

        Args:
            lane_densities: Per-lane density data.
            current_signal_plan: Current signal plan.
            emergency_active: Whether an emergency is active.
            corridor_status: Corridor metadata or None.
            inference_ms: Last inference latency.

        Returns:
            MQTT payload dictionary.
        """

        return {
            "intersection_id": self.config.intersection_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lane_densities": lane_densities,
            "current_signal_plan": current_signal_plan,
            "emergency_active": emergency_active,
            "corridor_status": corridor_status,
            "device_health": self._device_health(inference_ms),
        }

    def start_publishing(self, state_factory: Callable[[], dict[str, Any]], interval_seconds: int = 2) -> None:
        """Continuously publishes state snapshots.

        Args:
            state_factory: Callable returning the latest state payload.
            interval_seconds: Publish interval in seconds.

        Returns:
            None.
        """

        while True:
            payload = state_factory()
            self.publish_state(payload)
            time.sleep(interval_seconds)


def main() -> None:
    """Runs an MQTT publisher smoke test.

    Args:
        None.

    Returns:
        None.
    """

    publisher = EdgeMqttPublisher(load_config())
    payload = publisher.build_payload(
        lane_densities={"lane_1": {"count": 2, "queue_length": 1, "flow_rate": 3.0, "congestion_level": "LOW"}},
        current_signal_plan={"cycle_length": 60, "phases": [{"direction": "north-south", "green_duration": 30}]},
        emergency_active=False,
        corridor_status=None,
        inference_ms=14.6,
    )
    LOGGER.info("mqtt payload=%s", payload)


if __name__ == "__main__":
    main()
