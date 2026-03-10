from __future__ import annotations

from edge.density import DensitySnapshot, LaneDensity
from edge.optimizer import WebsterOptimizer


def test_webster_formula_known_input() -> None:
    snapshot = DensitySnapshot(
        timestamp="2026-03-10T00:00:00Z",
        lane_densities={
            "lane_1": LaneDensity(count=6, queue_length=3, flow_rate=6.0, congestion_level="MED"),
            "lane_2": LaneDensity(count=2, queue_length=1, flow_rate=2.0, congestion_level="LOW"),
            "lane_3": LaneDensity(count=4, queue_length=2, flow_rate=4.0, congestion_level="MED"),
            "lane_4": LaneDensity(count=1, queue_length=0, flow_rate=1.0, congestion_level="LOW"),
        },
    )
    optimizer = WebsterOptimizer()
    plan = optimizer.compute_plan(snapshot)
    assert plan.cycle_length == 51
    phase_map = {phase.direction: phase.green_duration for phase in plan.phases}
    assert phase_map["north-south"] == 26
    assert phase_map["east-west"] == 17
