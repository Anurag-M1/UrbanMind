from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.config import configure_logging, load_config
from edge.density import DensitySnapshot, LaneDensity


LOGGER = configure_logging(__name__)


@dataclass(slots=True)
class Phase:
    """Represents one signal phase allocation."""

    direction: str
    green_duration: int


@dataclass(slots=True)
class SignalPlan:
    """Represents the full signal timing plan."""

    cycle_length: int
    phases: list[Phase]

    def to_dict(self) -> dict[str, Any]:
        """Converts the signal plan to a dictionary.

        Args:
            None.

        Returns:
            Dictionary representation of the signal plan.
        """

        return {
            "cycle_length": self.cycle_length,
            "phases": [asdict(phase) for phase in self.phases],
        }


class WebsterOptimizer:
    """Computes adaptive signal timing using Webster's method."""

    def __init__(
        self,
        phase_lane_map: dict[str, list[str]] | None = None,
        lost_time_per_phase: int = 4,
        saturation_flow_per_lane: int = 1800,
    ) -> None:
        """Initializes the optimizer.

        Args:
            phase_lane_map: Mapping of phases to lane ids.
            lost_time_per_phase: Lost seconds per phase.
            saturation_flow_per_lane: Saturation flow per hour per lane.

        Returns:
            None.
        """

        self.phase_lane_map = phase_lane_map or {
            "north-south": ["lane_1", "lane_2"],
            "east-west": ["lane_3", "lane_4"],
        }
        self.lost_time_per_phase = lost_time_per_phase
        self.saturation_flow_per_lane = saturation_flow_per_lane

    def _critical_ratio(self, lane_density: LaneDensity) -> float:
        """Calculates the critical volume ratio for a lane.

        Args:
            lane_density: Density metrics for the lane.

        Returns:
            Critical ratio for Webster's formula.
        """

        vehicles_per_hour = max(
            lane_density.flow_rate * 120.0,
            lane_density.count * 120.0,
        )
        return vehicles_per_hour / float(self.saturation_flow_per_lane)

    def compute_plan(self, snapshot: DensitySnapshot) -> SignalPlan:
        """Computes a signal plan from density data.

        Args:
            snapshot: Latest lane density snapshot.

        Returns:
            Adaptive signal plan.
        """

        phase_ratios: dict[str, float] = {}
        for phase, lanes in self.phase_lane_map.items():
            phase_ratios[phase] = max(
                (self._critical_ratio(snapshot.lane_densities.get(lane, LaneDensity(0, 0, 0.0, "LOW"))) for lane in lanes),
                default=0.0,
            )

        lost_time = self.lost_time_per_phase * len(self.phase_lane_map)
        total_ratio = sum(phase_ratios.values())
        bounded_ratio = min(total_ratio, 0.95)

        if bounded_ratio <= 0:
            cycle_length = 40
            greens = {phase: max(10, int((cycle_length - lost_time) / len(self.phase_lane_map))) for phase in self.phase_lane_map}
        else:
            raw_cycle = (1.5 * lost_time + 5) / (1 - bounded_ratio)
            cycle_length = max(40, min(180, int(round(raw_cycle))))
            effective_green = max(0, cycle_length - lost_time)
            greens = {}
            for phase, ratio in phase_ratios.items():
                share = ratio / total_ratio if total_ratio else 1 / len(self.phase_lane_map)
                greens[phase] = max(10, min(90, int(round(effective_green * share))))

        effective_target = max(0, cycle_length - lost_time)
        delta = effective_target - sum(greens.values())
        phase_order = sorted(phase_ratios, key=phase_ratios.get, reverse=delta > 0)
        step = 1 if delta > 0 else -1
        while delta != 0 and phase_order:
            changed = False
            for phase in phase_order:
                candidate = greens[phase] + step
                if 10 <= candidate <= 90:
                    greens[phase] = candidate
                    delta -= step
                    changed = True
                    if delta == 0:
                        break
            if not changed:
                break

        return SignalPlan(
            cycle_length=cycle_length,
            phases=[Phase(direction=phase, green_duration=greens[phase]) for phase in self.phase_lane_map],
        )


def main() -> None:
    """Runs a sample Webster optimization.

    Args:
        None.

    Returns:
        None.
    """

    config = load_config()
    lane_densities = {
        f"lane_{index + 1}": LaneDensity(count=index + 2, queue_length=index, flow_rate=5.0 + index, congestion_level="MED")
        for index in range(config.lane_count)
    }
    snapshot = DensitySnapshot(timestamp="2026-03-10T00:00:00Z", lane_densities=lane_densities)
    plan = WebsterOptimizer().compute_plan(snapshot)
    LOGGER.info("signal plan=%s", plan.to_dict())


if __name__ == "__main__":
    main()
