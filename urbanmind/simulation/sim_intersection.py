from __future__ import annotations

import random
import sys
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.optimizer import Phase, SignalPlan, WebsterOptimizer


@dataclass(slots=True)
class SimulationMetrics:
    """Stores benchmark metrics for one simulated intersection."""

    average_wait_seconds: float
    optimal_wait_seconds: float


class SimulatedIntersection:
    """Simulates arrivals, queues, and adaptive signal timing for one intersection."""

    def __init__(self, intersection_id: str, lane_count: int = 4, start_time: datetime | None = None) -> None:
        """Initializes the intersection simulation.

        Args:
            intersection_id: Simulated intersection identifier.
            lane_count: Number of simulated lanes.
            start_time: Optional simulation start time.

        Returns:
            None.
        """

        self.intersection_id = intersection_id
        self.lane_count = lane_count
        self.optimizer = WebsterOptimizer()
        self.current_time = start_time or datetime.now(timezone.utc).replace(hour=8, minute=0, second=0, microsecond=0)
        self.queues: dict[str, deque[int]] = {f"lane_{index + 1}": deque() for index in range(lane_count)}
        self.departures: dict[str, deque[int]] = {lane_id: deque() for lane_id in self.queues}
        self.signal_plan = SignalPlan(
            cycle_length=60,
            phases=[
                Phase(direction="north-south", green_duration=30),
                Phase(direction="east-west", green_duration=22),
            ],
        )
        self.phase_index = 0
        self.phase_remaining = 30
        self.departure_carry = 0.0
        self.completed_waits: list[int] = []

    def _poisson_sample(self, lam: float) -> int:
        """Samples a Poisson random variable with Knuth's method.

        Args:
            lam: Expected value for the current second.

        Returns:
            Number of arrivals.
        """

        threshold = pow(2.718281828, -lam)
        product = 1.0
        count = 0
        while product > threshold:
            product *= random.random()
            count += 1
        return max(0, count - 1)

    def _arrival_rate_per_minute(self) -> int:
        """Returns the time-of-day arrival intensity.

        Args:
            None.

        Returns:
            Vehicles per minute for the current time.
        """

        hour = self.current_time.hour
        if 0 <= hour < 6:
            return 2
        if 6 <= hour < 9:
            return 18
        if 9 <= hour < 16:
            return 8
        if 16 <= hour < 19:
            return 20
        return 6

    def _phase_lanes(self) -> list[str]:
        """Returns lanes currently receiving green.

        Args:
            None.

        Returns:
            List of green lane ids.
        """

        if self.phase_index == 0:
            return ["lane_1", "lane_2"]
        return ["lane_3", "lane_4"]

    def _refresh_plan(self, second_elapsed: int) -> None:
        """Recomputes the Webster plan every 10 seconds.

        Args:
            second_elapsed: Simulation second count.

        Returns:
            None.
        """

        if second_elapsed % 10 != 0:
            return
        lane_densities = {}
        for lane_id, queue in self.queues.items():
            departures = [value for value in self.departures[lane_id] if second_elapsed - value <= 30]
            flow_rate = float(len(departures))
            count = len(queue)
            congestion = "HIGH" if count >= 8 else "MED" if count >= 4 else "LOW"
            lane_densities[lane_id] = type(
                "LaneDensityProxy",
                (),
                {
                    "count": count,
                    "queue_length": count,
                    "flow_rate": flow_rate,
                    "congestion_level": congestion,
                },
            )()
        snapshot = type("SnapshotProxy", (), {"lane_densities": lane_densities})()
        plan = self.optimizer.compute_plan(snapshot)
        self.signal_plan = plan
        self.phase_remaining = plan.phases[self.phase_index].green_duration

    def step(self, second_elapsed: int, emergency_active: bool = False) -> dict[str, Any]:
        """Advances the simulation by one second.

        Args:
            second_elapsed: Simulation second count.
            emergency_active: Whether emergency pre-emption is active.

        Returns:
            State payload matching the edge MQTT schema.
        """

        lam = self._arrival_rate_per_minute() / 60.0
        for lane_id in self.queues:
            arrivals = self._poisson_sample(lam)
            for _ in range(arrivals):
                self.queues[lane_id].append(second_elapsed)

        if emergency_active:
            green_lanes = ["lane_1", "lane_2"]
            self.phase_remaining = max(self.phase_remaining, 15)
        else:
            self._refresh_plan(second_elapsed)
            green_lanes = self._phase_lanes()

        self.departure_carry += 1800 / 3600
        departures_allowed = int(self.departure_carry)
        self.departure_carry -= departures_allowed
        for lane_id in green_lanes:
            for _ in range(departures_allowed):
                if self.queues[lane_id]:
                    arrival_second = self.queues[lane_id].popleft()
                    self.completed_waits.append(second_elapsed - arrival_second)
                    self.departures[lane_id].append(second_elapsed)

        self.phase_remaining -= 1
        if self.phase_remaining <= 0:
            self.phase_index = (self.phase_index + 1) % 2
            if isinstance(self.signal_plan, SignalPlan):
                self.phase_remaining = self.signal_plan.phases[self.phase_index].green_duration
            else:
                self.phase_remaining = 20

        self.current_time += timedelta(seconds=1)
        average_wait = sum(self.completed_waits[-120:]) / max(1, len(self.completed_waits[-120:]))
        optimal_wait = (self.signal_plan.cycle_length / 2) if isinstance(self.signal_plan, SignalPlan) else 30
        lane_densities: dict[str, dict[str, Any]] = {}
        for lane_id, queue in self.queues.items():
            departures = [value for value in self.departures[lane_id] if second_elapsed - value <= 30]
            count = len(queue)
            lane_densities[lane_id] = {
                "count": count,
                "queue_length": count,
                "flow_rate": float(len(departures)),
                "congestion_level": "HIGH" if count >= 8 else "MED" if count >= 4 else "LOW",
            }

        corridor_status = None
        if emergency_active:
            corridor_status = {
                "active": True,
                "vehicle_id": "SIM-AMB",
                "phase_overridden": "north-south",
                "estimated_clearance_seconds": max(10, self.phase_remaining),
            }

        return {
            "intersection_id": self.intersection_id,
            "timestamp": self.current_time.isoformat(),
            "lane_densities": lane_densities,
            "current_signal_plan": self.signal_plan.to_dict() if isinstance(self.signal_plan, SignalPlan) else {"cycle_length": 60, "phases": []},
            "emergency_active": emergency_active,
            "corridor_status": corridor_status,
            "device_health": {"cpu_pct": 12.0, "mem_pct": 20.0, "inference_ms": 0.0},
            "benchmark": {
                "actual_wait_seconds": round(average_wait, 2),
                "webster_optimal_wait_seconds": round(optimal_wait, 2),
            },
        }


def main() -> None:
    """Runs a short single-intersection simulation smoke test.

    Args:
        None.

    Returns:
        None.
    """

    simulator = SimulatedIntersection("sim_001")
    for second in range(5):
        print(simulator.step(second))


if __name__ == "__main__":
    main()
