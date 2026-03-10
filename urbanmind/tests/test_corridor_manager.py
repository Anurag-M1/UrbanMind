from __future__ import annotations

from backend.services.corridor_manager import CorridorManager, CorridorVehicle


def test_priority_queue_resolves_two_vehicle_conflict() -> None:
    manager = CorridorManager(
        {
            "intersection_001": (28.6139, 77.2090),
        }
    )
    manager.activate(
        CorridorVehicle(
            vehicle_id="AMB-1",
            vehicle_type="ambulance",
            gps_lat=28.6141,
            gps_lon=77.2091,
            route=["intersection_001"],
            corridor_id="corridor-AMB-1",
        )
    )
    manager.activate(
        CorridorVehicle(
            vehicle_id="FIRE-1",
            vehicle_type="fire",
            gps_lat=28.6200,
            gps_lon=77.2200,
            route=["intersection_001"],
            corridor_id="corridor-FIRE-1",
        )
    )
    assert manager.resolve_conflict("intersection_001") == "AMB-1"
