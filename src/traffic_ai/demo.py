from __future__ import annotations

import json

from .network import build_demo_network


def main() -> None:
    network = build_demo_network()

    network.ingest_detections(
        "J1",
        [
            {"lane_id": "J1_N", "label": "car", "bbox_area_ratio": 0.05, "speed_kph": 12},
            {"lane_id": "J1_N", "label": "bus", "bbox_area_ratio": 0.09, "speed_kph": 9},
            {
                "lane_id": "J1_S",
                "label": "ambulance",
                "bbox_area_ratio": 0.08,
                "speed_kph": 32,
            },
            {"lane_id": "J1_E", "label": "truck", "bbox_area_ratio": 0.07, "speed_kph": 6},
            {"lane_id": "J1_W", "label": "car", "bbox_area_ratio": 0.03, "speed_kph": 18},
        ],
    )
    network.ingest_detections(
        "J2",
        [
            {"lane_id": "J2_N", "label": "car", "bbox_area_ratio": 0.04, "speed_kph": 16},
            {"lane_id": "J2_S", "label": "car", "bbox_area_ratio": 0.04, "speed_kph": 14},
            {"lane_id": "J2_E", "label": "truck", "bbox_area_ratio": 0.08, "speed_kph": 7},
            {"lane_id": "J2_E", "label": "car", "bbox_area_ratio": 0.04, "speed_kph": 5},
            {"lane_id": "J2_W", "label": "bus", "bbox_area_ratio": 0.08, "speed_kph": 8},
        ],
    )
    network.ingest_detections(
        "J3",
        [
            {"lane_id": "J3_N", "label": "car", "bbox_area_ratio": 0.04, "speed_kph": 18},
            {"lane_id": "J3_S", "label": "car", "bbox_area_ratio": 0.03, "speed_kph": 20},
            {"lane_id": "J3_E", "label": "car", "bbox_area_ratio": 0.06, "speed_kph": 10},
            {"lane_id": "J3_W", "label": "car", "bbox_area_ratio": 0.05, "speed_kph": 11},
        ],
    )

    network.activate_green_corridor(
        {
            "vehicle_id": "AMB-12",
            "vehicle_type": "ambulance",
            "route": [
                {"intersection_id": "J1", "required_phase": "north_south", "eta_seconds": 12},
                {"intersection_id": "J2", "required_phase": "north_south", "eta_seconds": 28},
                {"intersection_id": "J3", "required_phase": "east_west", "eta_seconds": 44},
            ],
        }
    )

    print(json.dumps(network.snapshot(), indent=2))


if __name__ == "__main__":
    main()
