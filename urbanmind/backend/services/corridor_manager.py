from __future__ import annotations

import heapq
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class CorridorVehicle:
    """Represents an active emergency vehicle managed centrally."""

    vehicle_id: str
    vehicle_type: str
    gps_lat: float
    gps_lon: float
    route: list[str]
    corridor_id: str
    completed: set[str] = field(default_factory=set)


@dataclass(slots=True)
class CorridorStatus:
    """Represents the current pre-emption state for an emergency vehicle."""

    corridor_id: str
    vehicle_id: str
    vehicle_type: str
    route: list[str]
    pre_empted_intersections: list[str]
    updated_at: str
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Converts the status to a dictionary.

        Args:
            None.

        Returns:
            Dictionary representation.
        """

        return asdict(self)


class CorridorManager:
    """Maintains active emergency corridors and resolves conflicts."""

    def __init__(self, intersection_locations: dict[str, tuple[float, float]] | None = None) -> None:
        """Initializes the corridor manager.

        Args:
            intersection_locations: Mapping of intersection ids to coordinates.

        Returns:
            None.
        """

        self.intersection_locations = intersection_locations or {}
        self.active_vehicles: dict[str, CorridorVehicle] = {}
        self.intersection_queue: dict[str, list[tuple[float, str]]] = {}

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

    def _refresh_queue(self) -> None:
        """Rebuilds the intersection priority queues from active vehicles.

        Args:
            None.

        Returns:
            None.
        """

        self.intersection_queue = {}
        for vehicle in self.active_vehicles.values():
            for intersection_id in vehicle.route:
                if intersection_id in vehicle.completed:
                    continue
                coordinates = self.intersection_locations.get(intersection_id)
                if coordinates is None:
                    continue
                distance_m = self._distance_m(vehicle.gps_lat, vehicle.gps_lon, coordinates[0], coordinates[1])
                if distance_m <= 800:
                    self.intersection_queue.setdefault(intersection_id, [])
                    heapq.heappush(self.intersection_queue[intersection_id], (distance_m, vehicle.vehicle_id))

    def resolve_conflict(self, intersection_id: str) -> str | None:
        """Returns which vehicle currently has priority for an intersection.

        Args:
            intersection_id: Target intersection id.

        Returns:
            Winning vehicle id or None.
        """

        queue = self.intersection_queue.get(intersection_id, [])
        return queue[0][1] if queue else None

    def _build_status(self, vehicle: CorridorVehicle) -> CorridorStatus:
        """Builds a corridor status object for a vehicle.

        Args:
            vehicle: Emergency vehicle entry.

        Returns:
            Corridor status.
        """

        pre_empted = [
            intersection_id
            for intersection_id in vehicle.route
            if self.resolve_conflict(intersection_id) == vehicle.vehicle_id
        ]
        return CorridorStatus(
            corridor_id=vehicle.corridor_id,
            vehicle_id=vehicle.vehicle_id,
            vehicle_type=vehicle.vehicle_type,
            route=vehicle.route,
            pre_empted_intersections=pre_empted,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def activate(self, vehicle: CorridorVehicle) -> CorridorStatus:
        """Activates a new emergency corridor.

        Args:
            vehicle: Vehicle to activate.

        Returns:
            Corridor status.
        """

        self.active_vehicles[vehicle.vehicle_id] = vehicle
        self._refresh_queue()
        return self._build_status(vehicle)

    def update_position(self, vehicle_id: str, lat: float, lon: float) -> CorridorStatus:
        """Updates a vehicle position and recalculates its corridor.

        Args:
            vehicle_id: Vehicle identifier.
            lat: Latest latitude.
            lon: Latest longitude.

        Returns:
            Updated corridor status.
        """

        vehicle = self.active_vehicles[vehicle_id]
        vehicle.gps_lat = lat
        vehicle.gps_lon = lon
        for intersection_id in list(vehicle.route):
            coordinates = self.intersection_locations.get(intersection_id)
            if coordinates is None:
                continue
            distance_m = self._distance_m(lat, lon, coordinates[0], coordinates[1])
            if distance_m < 25:
                vehicle.completed.add(intersection_id)
        self._refresh_queue()
        return self._build_status(vehicle)

    def deactivate(self, vehicle_id: str) -> None:
        """Deactivates a corridor and removes its vehicle.

        Args:
            vehicle_id: Vehicle identifier.

        Returns:
            None.
        """

        self.active_vehicles.pop(vehicle_id, None)
        self._refresh_queue()

    def get_active_corridors(self) -> list[dict[str, Any]]:
        """Returns all currently active corridors.

        Args:
            None.

        Returns:
            List of corridor dictionaries.
        """

        return [self._build_status(vehicle).to_dict() for vehicle in self.active_vehicles.values()]

    def get_pre_empted_intersections(self) -> set[str]:
        """Returns the set of intersections currently under pre-emption.

        Args:
            None.

        Returns:
            Set of intersection ids.
        """

        return {intersection_id for intersection_id in self.intersection_queue if self.resolve_conflict(intersection_id) is not None}
