import json
import logging
import threading
from typing import Optional, Any

import paho.mqtt.client as mqtt

from config import settings

logger = logging.getLogger("urbanmind.mqtt")


class MQTTClient:
    def __init__(self) -> None:
        self.client: Optional[mqtt.Client] = None
        self.connected: bool = False
        self._thread: Optional[threading.Thread] = None

    def connect(self) -> None:
        """Connect to MQTT broker."""
        try:
            self.client = mqtt.Client(
                client_id="urbanmind-api",
                protocol=mqtt.MQTTv311,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            )
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            self.client.connect(
                settings.MQTT_HOST,
                settings.MQTT_PORT,
                keepalive=60,
            )
            self.client.loop_start()
            logger.info(
                "MQTT connecting to %s:%d", settings.MQTT_HOST, settings.MQTT_PORT
            )
        except Exception as e:
            logger.warning("MQTT connection failed (non-critical): %s", e)
            self.connected = False

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
            self.connected = False
            logger.info("MQTT disconnected")

    def publish(self, topic: str, payload: Any) -> None:
        """Publish a JSON message to a topic."""
        if not self.client or not self.connected:
            return
        try:
            message = json.dumps(payload) if not isinstance(payload, str) else payload
            self.client.publish(topic, message, qos=0)
        except Exception as e:
            logger.warning("MQTT publish error: %s", e)

    def subscribe(self, topic: str) -> None:
        """Subscribe to a topic."""
        if not self.client or not self.connected:
            return
        try:
            self.client.subscribe(topic, qos=0)
            logger.info("Subscribed to MQTT topic: %s", topic)
        except Exception as e:
            logger.warning("MQTT subscribe error: %s", e)

    def _on_connect(
        self, client: Any, userdata: Any, flags: Any, rc: Any, properties: Any = None
    ) -> None:
        if isinstance(rc, int):
            reason_code = rc
        else:
            reason_code = getattr(rc, "value", 0)

        if reason_code == 0:
            self.connected = True
            logger.info("MQTT connected successfully")
            # Subscribe to control topics
            self.subscribe("urbanmind/intersection/+/command")
            self.subscribe("urbanmind/emergency/#")
        else:
            self.connected = False
            logger.warning("MQTT connection refused: code=%s", reason_code)

    def _on_disconnect(
        self, client: Any, userdata: Any, flags: Any = None, rc: Any = None, properties: Any = None
    ) -> None:
        self.connected = False
        logger.warning("MQTT disconnected")

    def _on_message(
        self, client: Any, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug("MQTT message on %s: %s", msg.topic, payload)
        except Exception:
            pass


mqtt_client = MQTTClient()
