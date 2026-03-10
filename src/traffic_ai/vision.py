from __future__ import annotations

from collections import defaultdict

from .models import Detection, EMERGENCY_LABELS, HEAVY_LABELS, Intersection, LaneMetrics


class VisionTrafficAnalyzer:
    """Converts camera detections into lane-level traffic features."""

    def analyze(self, intersection: Intersection, detections: list[Detection]) -> dict[str, LaneMetrics]:
        grouped: dict[str, list[Detection]] = defaultdict(list)
        for detection in detections:
            if detection.lane_id in intersection.lane_phase_map:
                grouped[detection.lane_id].append(detection)

        lane_metrics: dict[str, LaneMetrics] = {}
        for lane_id in intersection.lane_phase_map:
            lane_detections = grouped.get(lane_id, [])
            speeds = [item.speed_kph for item in lane_detections if item.speed_kph is not None]
            avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
            occupied_ratio = min(1.0, sum(item.bbox_area_ratio for item in lane_detections))
            heavy_count = sum(
                1 for item in lane_detections if item.normalized_label() in HEAVY_LABELS
            )
            emergency_detected = any(
                item.normalized_label() in EMERGENCY_LABELS for item in lane_detections
            )
            stopped_count = sum(
                1
                for item in lane_detections
                if item.speed_kph is not None and item.speed_kph < 5.0
            )
            queue_length_m = (stopped_count * 6.0) + (occupied_ratio * 24.0)
            lane_metrics[lane_id] = LaneMetrics(
                lane_id=lane_id,
                direction=intersection.directions[lane_id],
                vehicle_count=len(lane_detections),
                heavy_vehicle_count=heavy_count,
                occupied_ratio=round(occupied_ratio, 3),
                average_speed_kph=round(avg_speed, 2),
                queue_length_m=round(queue_length_m, 2),
                emergency_vehicle_detected=emergency_detected,
            )
        return lane_metrics
