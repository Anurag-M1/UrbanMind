from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s"


@dataclass(slots=True)
class IntersectionLocation:
    """Represents an intersection's geographic position."""

    intersection_id: str
    lat: float
    lon: float


@dataclass(slots=True)
class EdgeConfig:
    """Stores runtime configuration for an edge node."""

    intersection_id: str
    rtsp_stream_url: str
    lane_count: int
    mqtt_host: str
    mqtt_port: int
    signal_controller_url: str
    stub_mode: bool
    debug: bool
    yolo_model_path: str
    siren_model_path: str
    log_level: str
    target_fps: int = 15
    confidence_threshold: float = 0.65
    city_center_lat: float = 28.6139
    city_center_lon: float = 77.2090
    phase_order: tuple[str, ...] = ("north-south", "east-west")
    intersection_locations: dict[str, IntersectionLocation] = field(default_factory=dict)
    approach_phase_map: dict[str, str] = field(default_factory=dict)


def _load_dotenv_file() -> None:
    """Loads environment variables from a local .env file when available.

    Args:
        None.

    Returns:
        None.
    """

    if load_dotenv is None:
        return
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def configure_logging(module_name: str) -> logging.Logger:
    """Configures and returns a module logger.

    Args:
        module_name: Name of the logger to create.

    Returns:
        A configured logger instance.
    """

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format=LOG_FORMAT)
    return logging.getLogger(module_name)


def _parse_bool(value: str | None, default: bool) -> bool:
    """Parses a boolean environment variable.

    Args:
        value: Raw environment variable value.
        default: Fallback value when parsing fails.

    Returns:
        The parsed boolean.
    """

    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_locations(raw_value: str | None) -> dict[str, IntersectionLocation]:
    """Parses intersection coordinates from JSON.

    Args:
        raw_value: JSON mapping of intersection ids to coordinates.

    Returns:
        Mapping of intersection ids to location objects.
    """

    if not raw_value:
        return {}
    parsed: dict[str, Any] = json.loads(raw_value)
    return {
        intersection_id: IntersectionLocation(
            intersection_id=intersection_id,
            lat=float(value["lat"]),
            lon=float(value["lon"]),
        )
        for intersection_id, value in parsed.items()
    }


def _parse_mapping(raw_value: str | None) -> dict[str, str]:
    """Parses a string-to-string JSON mapping from environment variables.

    Args:
        raw_value: JSON encoded mapping.

    Returns:
        Parsed mapping.
    """

    if not raw_value:
        return {}
    return {str(key): str(value) for key, value in json.loads(raw_value).items()}


def load_config() -> EdgeConfig:
    """Loads edge configuration from environment variables.

    Args:
        None.

    Returns:
        An EdgeConfig instance.
    """

    _load_dotenv_file()
    intersection_locations = _parse_locations(os.getenv("INTERSECTION_LOCATIONS_JSON"))
    return EdgeConfig(
        intersection_id=os.getenv("INTERSECTION_ID", "intersection_001"),
        rtsp_stream_url=os.getenv("RTSP_STREAM_URL", "rtsp://127.0.0.1:8554/stream"),
        lane_count=int(os.getenv("LANE_COUNT", "4")),
        mqtt_host=os.getenv("MQTT_HOST", "127.0.0.1"),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        signal_controller_url=os.getenv("SIGNAL_CONTROLLER_URL", "http://127.0.0.1:8081"),
        stub_mode=_parse_bool(os.getenv("STUB_MODE"), True),
        debug=_parse_bool(os.getenv("DEBUG"), False),
        yolo_model_path=os.getenv("YOLO_MODEL_PATH", "models/yolov8n.pt"),
        siren_model_path=os.getenv("SIREN_MODEL_PATH", "models/siren_cnn.pt"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        target_fps=int(os.getenv("TARGET_FPS", "15")),
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.65")),
        city_center_lat=float(os.getenv("CITY_CENTER_LAT", "28.6139")),
        city_center_lon=float(os.getenv("CITY_CENTER_LON", "77.2090")),
        intersection_locations=intersection_locations,
        approach_phase_map=_parse_mapping(os.getenv("APPROACH_PHASE_MAP_JSON")),
    )


def main() -> None:
    """Prints the current edge configuration for smoke testing.

    Args:
        None.

    Returns:
        None.
    """

    logger = configure_logging(__name__)
    logger.info("Loaded edge config: %s", load_config())


if __name__ == "__main__":
    main()
