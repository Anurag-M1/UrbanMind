from __future__ import annotations

from edge.config import EdgeConfig, IntersectionLocation
from edge.corridor import EmergencyVehicle, GreenCorridorManager


def _config() -> EdgeConfig:
    return EdgeConfig(
        intersection_id="intersection_001",
        rtsp_stream_url="rtsp://example/stream",
        lane_count=4,
        mqtt_host="localhost",
        mqtt_port=1883,
        signal_controller_url="http://localhost:8080",
        stub_mode=True,
        debug=False,
        yolo_model_path="models/yolov8n.pt",
        siren_model_path="models/siren_cnn.pt",
        log_level="INFO",
        intersection_locations={
            "intersection_001": IntersectionLocation("intersection_001", 28.6139, 77.2090),
            "intersection_002": IntersectionLocation("intersection_002", 28.6150, 77.2100),
        },
        approach_phase_map={"intersection_001": "north-south", "intersection_002": "east-west"},
    )


def test_pre_emption_activates_within_800m_and_deactivates_after_pass() -> None:
    manager = GreenCorridorManager(_config())
    statuses = manager.activate(
        EmergencyVehicle(
            id="AMB-1",
            gps_lat=28.6140,
            gps_lon=77.2091,
            vehicle_type="ambulance",
            route=["intersection_001", "intersection_002"],
        )
    )
    assert any(status.intersection_id == "intersection_001" for status in statuses)

    updated = manager.update_vehicle_position("AMB-1", 28.6160, 77.2110)
    assert all(status.intersection_id != "intersection_001" for status in updated)
