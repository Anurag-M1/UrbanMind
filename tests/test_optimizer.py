from __future__ import annotations

import unittest

from traffic_ai.network import build_demo_network


class AdaptiveSignalControllerTests(unittest.TestCase):
    def test_heavier_north_south_pressure_gets_more_green(self) -> None:
        network = build_demo_network()
        state = network.ingest_detections(
            "J1",
            [
                {"lane_id": "J1_N", "label": "car", "bbox_area_ratio": 0.08, "speed_kph": 4},
                {"lane_id": "J1_N", "label": "truck", "bbox_area_ratio": 0.09, "speed_kph": 3},
                {"lane_id": "J1_S", "label": "bus", "bbox_area_ratio": 0.08, "speed_kph": 4},
                {"lane_id": "J1_E", "label": "car", "bbox_area_ratio": 0.03, "speed_kph": 25},
            ],
        )

        plan = state["phase_plan"]
        self.assertGreater(plan["north_south"], plan["east_west"])

    def test_emergency_vehicle_increases_lane_pressure(self) -> None:
        network = build_demo_network()
        state = network.ingest_detections(
            "J1",
            [
                {"lane_id": "J1_N", "label": "ambulance", "bbox_area_ratio": 0.08, "speed_kph": 30},
                {"lane_id": "J1_E", "label": "car", "bbox_area_ratio": 0.08, "speed_kph": 5},
            ],
        )

        lane_metrics = state["lane_metrics"]
        self.assertTrue(lane_metrics["J1_N"]["emergency_vehicle_detected"])
        self.assertGreater(
            lane_metrics["J1_N"]["pressure_score"],
            lane_metrics["J1_E"]["pressure_score"],
        )


if __name__ == "__main__":
    unittest.main()
