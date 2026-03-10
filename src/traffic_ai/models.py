from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


EMERGENCY_LABELS = {"ambulance", "fire_truck", "fire_engine", "police"}
HEAVY_LABELS = {"bus", "truck", "fire_truck", "fire_engine"}


@dataclass(slots=True)
class Detection:
    lane_id: str
    label: str
    bbox_area_ratio: float
    speed_kph: float | None = None
    confidence: float = 1.0

    def normalized_label(self) -> str:
        return self.label.strip().lower()


@dataclass(slots=True)
class LaneMetrics:
    lane_id: str
    direction: str
    vehicle_count: int = 0
    heavy_vehicle_count: int = 0
    occupied_ratio: float = 0.0
    average_speed_kph: float = 0.0
    queue_length_m: float = 0.0
    emergency_vehicle_detected: bool = False

    def pressure_score(self) -> float:
        congestion_penalty = max(0.0, 1.0 - min(self.average_speed_kph / 50.0, 1.0))
        return (
            (self.vehicle_count * 1.6)
            + (self.heavy_vehicle_count * 1.2)
            + (self.occupied_ratio * 30.0)
            + (self.queue_length_m * 0.22)
            + (congestion_penalty * 15.0)
            + (20.0 if self.emergency_vehicle_detected else 0.0)
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pressure_score"] = round(self.pressure_score(), 2)
        return data


@dataclass(slots=True)
class Intersection:
    intersection_id: str
    lane_phase_map: dict[str, str]
    directions: dict[str, str]
    cycle_seconds: int = 120
    min_green_seconds: int = 15
    max_green_seconds: int = 80
    yellow_seconds: int = 4
    all_red_seconds: int = 2
    current_phase: str = "north_south"
    lane_metrics: dict[str, LaneMetrics] = field(default_factory=dict)
    phase_plan: dict[str, int] = field(default_factory=dict)
    emergency_override: dict[str, Any] | None = None

    def phases(self) -> list[str]:
        return sorted(set(self.lane_phase_map.values()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "intersection_id": self.intersection_id,
            "current_phase": self.current_phase,
            "cycle_seconds": self.cycle_seconds,
            "phase_plan": self.phase_plan,
            "emergency_override": self.emergency_override,
            "lane_metrics": {
                lane_id: metrics.to_dict()
                for lane_id, metrics in sorted(self.lane_metrics.items())
            },
        }


@dataclass(slots=True, frozen=True)
class CorridorWaypoint:
    intersection_id: str
    required_phase: str
    eta_seconds: int
    hold_seconds: int = 25


@dataclass(slots=True, frozen=True)
class EmergencyRouteRequest:
    vehicle_id: str
    vehicle_type: str
    route: tuple[CorridorWaypoint, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "EmergencyRouteRequest":
        route = tuple(
            CorridorWaypoint(
                intersection_id=item["intersection_id"],
                required_phase=item["required_phase"],
                eta_seconds=int(item["eta_seconds"]),
                hold_seconds=int(item.get("hold_seconds", 25)),
            )
            for item in payload["route"]
        )
        return cls(
            vehicle_id=payload["vehicle_id"],
            vehicle_type=payload["vehicle_type"],
            route=route,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
