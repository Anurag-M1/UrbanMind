from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EmergencyGpsPoint:
    """Stores the latest GPS point for an emergency vehicle."""

    vehicle_id: str
    lat: float
    lon: float


class EmergencyGpsTracker:
    """Tracks the latest known GPS positions for active emergency vehicles."""

    def __init__(self) -> None:
        """Initializes the tracker.

        Args:
            None.

        Returns:
            None.
        """

        self.positions: dict[str, EmergencyGpsPoint] = {}

    def upsert(self, vehicle_id: str, lat: float, lon: float) -> EmergencyGpsPoint:
        """Stores or updates a vehicle position.

        Args:
            vehicle_id: Vehicle identifier.
            lat: Latest latitude.
            lon: Latest longitude.

        Returns:
            Stored GPS point.
        """

        point = EmergencyGpsPoint(vehicle_id=vehicle_id, lat=lat, lon=lon)
        self.positions[vehicle_id] = point
        return point

    def remove(self, vehicle_id: str) -> None:
        """Removes a tracked vehicle position.

        Args:
            vehicle_id: Vehicle identifier.

        Returns:
            None.
        """

        self.positions.pop(vehicle_id, None)

    def get(self, vehicle_id: str) -> EmergencyGpsPoint | None:
        """Fetches a tracked vehicle position.

        Args:
            vehicle_id: Vehicle identifier.

        Returns:
            GPS point or None.
        """

        return self.positions.get(vehicle_id)
