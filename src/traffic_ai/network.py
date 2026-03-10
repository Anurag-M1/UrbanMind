from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import Detection, EmergencyRouteRequest, Intersection
from .optimizer import AdaptiveSignalController
from .vision import VisionTrafficAnalyzer


class EmergencyCorridorManager:
    """Preempts normal plans to create a continuous green corridor."""

    def apply(self, network: "TrafficNetwork", request: EmergencyRouteRequest) -> dict[str, Any]:
        commands: list[dict[str, Any]] = []
        for waypoint in request.route:
            intersection = network.intersections.get(waypoint.intersection_id)
            if intersection is None:
                continue

            base_plan = intersection.phase_plan or network.controller.plan_cycle(intersection)
            override_plan = dict(base_plan)
            for phase in intersection.phases():
                if phase == waypoint.required_phase:
                    override_plan[phase] = min(
                        intersection.max_green_seconds,
                        max(base_plan.get(phase, 0), waypoint.hold_seconds),
                    )
                else:
                    override_plan[phase] = intersection.min_green_seconds

            intersection.phase_plan = override_plan
            intersection.current_phase = waypoint.required_phase
            intersection.emergency_override = {
                "vehicle_id": request.vehicle_id,
                "vehicle_type": request.vehicle_type,
                "required_phase": waypoint.required_phase,
                "activate_in_seconds": max(0, waypoint.eta_seconds - 8),
                "hold_seconds": waypoint.hold_seconds,
            }
            commands.append(
                {
                    "intersection_id": intersection.intersection_id,
                    "command": "PREEMPT_GREEN",
                    "phase": waypoint.required_phase,
                    "activate_in_seconds": intersection.emergency_override["activate_in_seconds"],
                    "hold_seconds": waypoint.hold_seconds,
                    "plan": override_plan,
                }
            )

        return {
            "vehicle_id": request.vehicle_id,
            "vehicle_type": request.vehicle_type,
            "commands": commands,
            "route": [asdict(waypoint) for waypoint in request.route],
        }


class TrafficNetwork:
    def __init__(self, intersections: list[Intersection]) -> None:
        self.intersections = {
            intersection.intersection_id: intersection for intersection in intersections
        }
        self.vision = VisionTrafficAnalyzer()
        self.controller = AdaptiveSignalController()
        self.corridor = EmergencyCorridorManager()

    def ingest_detections(
        self, intersection_id: str, detections: list[dict[str, Any]]
    ) -> dict[str, Any]:
        intersection = self.intersections[intersection_id]
        parsed = [
            Detection(
                lane_id=item["lane_id"],
                label=item["label"],
                bbox_area_ratio=float(item.get("bbox_area_ratio", 0.0)),
                speed_kph=(
                    None
                    if item.get("speed_kph") is None
                    else float(item.get("speed_kph"))
                ),
                confidence=float(item.get("confidence", 1.0)),
            )
            for item in detections
        ]
        intersection.lane_metrics = self.vision.analyze(intersection, parsed)
        intersection.phase_plan = self.controller.plan_cycle(intersection)
        intersection.emergency_override = None
        return intersection.to_dict()

    def optimize(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for intersection in self.intersections.values():
            intersection.phase_plan = self.controller.plan_cycle(intersection)
            results[intersection.intersection_id] = intersection.to_dict()
        return results

    def activate_green_corridor(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = EmergencyRouteRequest.from_payload(payload)
        return self.corridor.apply(self, request)

    def snapshot(self) -> dict[str, Any]:
        return {
            "intersections": {
                intersection_id: intersection.to_dict()
                for intersection_id, intersection in sorted(self.intersections.items())
            }
        }


def build_demo_network() -> TrafficNetwork:
    intersections = [
        Intersection(
            intersection_id="J1",
            lane_phase_map={
                "J1_N": "north_south",
                "J1_S": "north_south",
                "J1_E": "east_west",
                "J1_W": "east_west",
            },
            directions={
                "J1_N": "north",
                "J1_S": "south",
                "J1_E": "east",
                "J1_W": "west",
            },
        ),
        Intersection(
            intersection_id="J2",
            lane_phase_map={
                "J2_N": "north_south",
                "J2_S": "north_south",
                "J2_E": "east_west",
                "J2_W": "east_west",
            },
            directions={
                "J2_N": "north",
                "J2_S": "south",
                "J2_E": "east",
                "J2_W": "west",
            },
        ),
        Intersection(
            intersection_id="J3",
            lane_phase_map={
                "J3_N": "north_south",
                "J3_S": "north_south",
                "J3_E": "east_west",
                "J3_W": "east_west",
            },
            directions={
                "J3_N": "north",
                "J3_S": "south",
                "J3_E": "east",
                "J3_W": "west",
            },
        ),
    ]
    return TrafficNetwork(intersections)
