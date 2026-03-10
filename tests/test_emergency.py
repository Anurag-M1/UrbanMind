from __future__ import annotations

import unittest

from traffic_ai.network import build_demo_network


class EmergencyCorridorTests(unittest.TestCase):
    def test_route_intersections_receive_required_phase_override(self) -> None:
        network = build_demo_network()
        network.optimize()

        result = network.activate_green_corridor(
            {
                "vehicle_id": "FIRE-2",
                "vehicle_type": "fire_truck",
                "route": [
                    {"intersection_id": "J1", "required_phase": "north_south", "eta_seconds": 10},
                    {"intersection_id": "J2", "required_phase": "north_south", "eta_seconds": 24},
                    {"intersection_id": "J3", "required_phase": "east_west", "eta_seconds": 41},
                ],
            }
        )

        self.assertEqual(len(result["commands"]), 3)

        j1 = network.snapshot()["intersections"]["J1"]
        j3 = network.snapshot()["intersections"]["J3"]
        self.assertEqual(j1["current_phase"], "north_south")
        self.assertEqual(j3["current_phase"], "east_west")
        self.assertGreaterEqual(j1["phase_plan"]["north_south"], 25)
        self.assertEqual(j1["phase_plan"]["east_west"], 15)
        self.assertEqual(j3["phase_plan"]["north_south"], 15)


if __name__ == "__main__":
    unittest.main()
