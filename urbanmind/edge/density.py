from __future__ import annotations

import sys
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.config import configure_logging, load_config
from edge.detector import Detection


LOGGER = configure_logging(__name__)


@dataclass(slots=True)
class LaneDensity:
    """Stores congestion metrics for one lane."""

    count: int
    queue_length: int
    flow_rate: float
    congestion_level: str


@dataclass(slots=True)
class DensitySnapshot:
    """Stores a timestamped set of lane densities."""

    timestamp: str
    lane_densities: dict[str, LaneDensity]

    def to_dict(self) -> dict[str, Any]:
        """Converts the snapshot to a JSON-serializable structure.

        Args:
            None.

        Returns:
            Dictionary representation of the snapshot.
        """

        return {
            "timestamp": self.timestamp,
            "lane_densities": {
                lane_id: asdict(lane_density)
                for lane_id, lane_density in sorted(self.lane_densities.items())
            },
        }


class DensityEstimator:
    """Computes lane counts, queues, and flow rates from frame detections."""

    def __init__(self, lane_count: int) -> None:
        """Initializes estimator state.

        Args:
            lane_count: Number of vertical lane zones.

        Returns:
            None.
        """

        self.lane_count = lane_count
        self.crossing_history: dict[str, deque[tuple[float, str]]] = {
            f"lane_{index + 1}": deque() for index in range(lane_count)
        }
        self.last_seen_centers: dict[str, set[str]] = {lane_id: set() for lane_id in self.crossing_history}

    def _line_key(self, detection: Detection) -> str:
        """Builds a stable crossing key for a detection center.

        Args:
            detection: Detection to encode.

        Returns:
            Quantized key string.
        """

        x1, y1, x2, y2 = detection.bbox
        center_x = int((x1 + x2) / 2 // 10)
        center_y = int((y1 + y2) / 2 // 10)
        return f"{center_x}:{center_y}:{detection.class_name}"

    def _congestion_level(self, count: int, queue_length: int, flow_rate: float) -> str:
        """Classifies lane congestion.

        Args:
            count: Current vehicle count.
            queue_length: Stopped vehicles near the stop line.
            flow_rate: Vehicles passing the virtual line per 30 seconds.

        Returns:
            Congestion label.
        """

        if queue_length >= 5 or count >= 8 or flow_rate >= 12:
            return "HIGH"
        if queue_length >= 2 or count >= 4 or flow_rate >= 6:
            return "MED"
        return "LOW"

    def update(
        self,
        detections: list[Detection],
        frame_shape: tuple[int, int],
        timestamp: datetime | None = None,
    ) -> DensitySnapshot:
        """Updates density metrics using detections from one frame.

        Args:
            detections: Per-frame detections.
            frame_shape: Height and width of the frame.
            timestamp: Optional event time.

        Returns:
            Density snapshot for the current frame.
        """

        event_time = timestamp or datetime.now(timezone.utc)
        frame_height, _ = frame_shape
        bottom_threshold = frame_height * 0.6
        crossing_line = frame_height * 0.5
        by_lane: dict[str, list[Detection]] = {lane_id: [] for lane_id in self.crossing_history}
        for detection in detections:
            by_lane.setdefault(detection.lane_id, []).append(detection)

        lane_densities: dict[str, LaneDensity] = {}
        for lane_id, lane_detections in by_lane.items():
            queue_length = 0
            for detection in lane_detections:
                _, y1, _, y2 = detection.bbox
                center_y = (y1 + y2) / 2
                if center_y >= bottom_threshold:
                    queue_length += 1
                if center_y >= crossing_line:
                    event_key = self._line_key(detection)
                    if event_key not in self.last_seen_centers[lane_id]:
                        self.last_seen_centers[lane_id].add(event_key)
                        self.crossing_history[lane_id].append((event_time.timestamp(), event_key))

            while (
                self.crossing_history[lane_id]
                and event_time.timestamp() - self.crossing_history[lane_id][0][0] > 30
            ):
                _, expired_key = self.crossing_history[lane_id].popleft()
                self.last_seen_centers[lane_id].discard(expired_key)

            flow_rate = float(len(self.crossing_history[lane_id]))
            count = len(lane_detections)
            lane_densities[lane_id] = LaneDensity(
                count=count,
                queue_length=queue_length,
                flow_rate=flow_rate,
                congestion_level=self._congestion_level(count, queue_length, flow_rate),
            )
        return DensitySnapshot(timestamp=event_time.isoformat(), lane_densities=lane_densities)


def main() -> None:
    """Runs a density estimation smoke test with synthetic detections.

    Args:
        None.

    Returns:
        None.
    """

    config = load_config()
    estimator = DensityEstimator(config.lane_count)
    detections = [
        Detection(class_name="car", bbox=(10, 120, 80, 220), confidence=0.9, lane_id="lane_1"),
        Detection(class_name="bus", bbox=(120, 250, 210, 380), confidence=0.91, lane_id="lane_2"),
    ]
    snapshot = estimator.update(detections, frame_shape=(480, 640))
    LOGGER.info("density snapshot=%s", snapshot.to_dict())


if __name__ == "__main__":
    main()
