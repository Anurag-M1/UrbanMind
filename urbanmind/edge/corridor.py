from __future__ import annotations

import heapq
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.config import EdgeConfig, configure_logging, load_config


LOGGER = configure_logging(__name__)


@dataclass(slots=True)
class EmergencyVehicle:
    """Represents an active emergency vehicle."""

    id: str
    gps_lat: float
    gps_lon: float
    vehicle_type: str
    route: list[str]
    completed_intersections: set[str] = field(default_factory=set)
    last_distances: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class CorridorStatus:
    """Represents corridor pre-emption status for one intersection."""

    active: bool
    vehicle_id: str
    phase_overridden: str
    estimated_clearance_seconds: int
    intersection_id: str
    distance_m: float

    def to_dict(self) -> dict[str, Any]:
        """Converts the status to a dictionary.

        Args:
            None.

        Returns:
            Dictionary representation of the status.
        """

        return asdict(self)


class GreenCorridorManager:
    """Handles emergency corridor activation and conflict resolution."""

    def __init__(self, config: EdgeConfig) -> None:
        """Initializes the corridor manager.

        Args:
            config: Edge runtime configuration.

        Returns:
            None.
        """

        self.config = config
        self.vehicles: dict[str, EmergencyVehicle] = {}
        self.heaps: dict[str, list[tuple[float, str]]] = {}

    def _distance_m(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates haversine distance between two coordinates.

        Args:
            lat1: First latitude.
            lon1: First longitude.
            lat2: Second latitude.
            lon2: Second longitude.

        Returns:
            Distance in meters.
        """

        radius = 6_371_000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)
        a = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _rebuild_heaps(self) -> None:
        """Rebuilds the per-intersection priority queues.

        Args:
            None.

        Returns:
            None.
        """

        self.heaps = {}
        for vehicle in self.vehicles.values():
            for intersection_id in vehicle.route:
                if intersection_id in vehicle.completed_intersections:
                    continue
                location = self.config.intersection_locations.get(intersection_id)
                if location is None:
                    continue
                distance_m = self._distance_m(vehicle.gps_lat, vehicle.gps_lon, location.lat, location.lon)
                if distance_m <= 800:
                    self.heaps.setdefault(intersection_id, [])
                    heapq.heappush(self.heaps[intersection_id], (distance_m, vehicle.id))

    def resolve_conflict(self, intersection_id: str) -> str | None:
        """Resolves which vehicle gets pre-emption priority for an intersection.

        Args:
            intersection_id: Intersection being contested.

        Returns:
            Winning vehicle id or None.
        """

        queue = self.heaps.get(intersection_id, [])
        if not queue:
            return None
        if len(queue) > 1:
            LOGGER.info("corridor conflict at %s resolved in favour of %s", intersection_id, queue[0][1])
        return queue[0][1]

    def activate(self, vehicle: EmergencyVehicle) -> list[CorridorStatus]:
        """Adds an emergency vehicle and evaluates its corridor.

        Args:
            vehicle: Emergency vehicle to activate.

        Returns:
            Corridor statuses for all affected intersections.
        """

        for intersection_id in vehicle.route:
            location = self.config.intersection_locations.get(intersection_id)
            if location is None:
                continue
            vehicle.last_distances[intersection_id] = self._distance_m(
                vehicle.gps_lat,
                vehicle.gps_lon,
                location.lat,
                location.lon,
            )
        self.vehicles[vehicle.id] = vehicle
        self._rebuild_heaps()
        return self.get_statuses()

    def update_vehicle_position(self, vehicle_id: str, lat: float, lon: float) -> list[CorridorStatus]:
        """Updates GPS position and recalculates pre-emption.

        Args:
            vehicle_id: Vehicle identifier.
            lat: Latest latitude.
            lon: Latest longitude.

        Returns:
            Updated corridor statuses.
        """

        vehicle = self.vehicles[vehicle_id]
        vehicle.gps_lat = lat
        vehicle.gps_lon = lon
        for intersection_id in vehicle.route:
            if intersection_id in vehicle.completed_intersections:
                continue
            location = self.config.intersection_locations.get(intersection_id)
            if location is None:
                continue
            distance_m = self._distance_m(lat, lon, location.lat, location.lon)
            previous_distance = vehicle.last_distances.get(intersection_id)
            if distance_m < 30 or (previous_distance is not None and previous_distance < 80 and distance_m > previous_distance + 50):
                vehicle.completed_intersections.add(intersection_id)
            vehicle.last_distances[intersection_id] = distance_m
        self._rebuild_heaps()
        return self.get_statuses()

    def deactivate(self, vehicle_id: str) -> None:
        """Removes an active emergency vehicle.

        Args:
            vehicle_id: Vehicle identifier.

        Returns:
            None.
        """

        self.vehicles.pop(vehicle_id, None)
        self._rebuild_heaps()

    def get_statuses(self) -> list[CorridorStatus]:
        """Returns active corridor statuses across all intersections.

        Args:
            None.

        Returns:
            List of active statuses.
        """

        statuses: list[CorridorStatus] = []
        for intersection_id, queue in sorted(self.heaps.items()):
            if not queue:
                continue
            distance_m, vehicle_id = queue[0]
            phase_direction = self.config.approach_phase_map.get(intersection_id, "north-south")
            statuses.append(
                CorridorStatus(
                    active=True,
                    vehicle_id=vehicle_id,
                    phase_overridden=phase_direction,
                    estimated_clearance_seconds=max(10, int(distance_m / 12)),
                    intersection_id=intersection_id,
                    distance_m=round(distance_m, 2),
                )
            )
        return statuses


def main() -> None:
    """Runs a green corridor smoke test.

    Args:
        None.

    Returns:
        None.
    """

    manager = GreenCorridorManager(load_config())
    statuses = manager.activate(
        EmergencyVehicle(
            id="AMB-1",
            gps_lat=28.6140,
            gps_lon=77.2091,
            vehicle_type="ambulance",
            route=["intersection_001", "intersection_002"],
        )
    )
    LOGGER.info("corridor_status=%s", [status.to_dict() for status in statuses])


if __name__ == "__main__":
    main()
