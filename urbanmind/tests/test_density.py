from __future__ import annotations

from edge.density import DensityEstimator
from edge.detector import Detection


def test_congestion_thresholds() -> None:
    estimator = DensityEstimator(lane_count=4)
    detections = [
        Detection(class_name="car", bbox=(0, 260, 60, 380), confidence=0.9, lane_id="lane_1"),
        Detection(class_name="car", bbox=(0, 280, 60, 400), confidence=0.9, lane_id="lane_1"),
        Detection(class_name="car", bbox=(0, 300, 60, 420), confidence=0.9, lane_id="lane_1"),
        Detection(class_name="car", bbox=(0, 320, 60, 440), confidence=0.9, lane_id="lane_1"),
        Detection(class_name="car", bbox=(0, 340, 60, 460), confidence=0.9, lane_id="lane_1"),
    ]
    snapshot = estimator.update(detections, frame_shape=(480, 640))
    assert snapshot.lane_densities["lane_1"].queue_length == 5
    assert snapshot.lane_densities["lane_1"].congestion_level == "HIGH"
