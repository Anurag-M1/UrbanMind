"""
UrbanMind — Lane ROI (Region of Interest) Masking
Utilities for defining and applying ROI zones per lane at each intersection.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("urbanmind.lane_roi")


@dataclass
class ROI:
    """Region of Interest defined by normalized coordinates (0-1)."""
    x1: float
    y1: float
    x2: float
    y2: float

    def to_pixels(self, width: int, height: int) -> Tuple[int, int, int, int]:
        """Convert normalized ROI to pixel coordinates."""
        return (
            int(self.x1 * width),
            int(self.y1 * height),
            int(self.x2 * width),
            int(self.y2 * height),
        )

    def contains_point(self, x: float, y: float, width: int, height: int) -> bool:
        """Check if a pixel coordinate falls within this ROI."""
        px1, py1, px2, py2 = self.to_pixels(width, height)
        return px1 <= x <= px2 and py1 <= y <= py2

    def contains_normalized(self, nx: float, ny: float) -> bool:
        """Check if a normalized coordinate falls within this ROI."""
        return self.x1 <= nx <= self.x2 and self.y1 <= ny <= self.y2

    def area_pixels(self, width: int, height: int) -> int:
        """Calculate ROI area in pixels."""
        px1, py1, px2, py2 = self.to_pixels(width, height)
        return abs(px2 - px1) * abs(py2 - py1)


# Default ROI layouts for standard 4-way Indian intersections
# These assume a typical overhead camera angle
DEFAULT_ROIS: Dict[str, ROI] = {
    "ew_in": ROI(x1=0.0, y1=0.3, x2=0.35, y2=0.7),    # E-W incoming (left side)
    "ew_out": ROI(x1=0.65, y1=0.3, x2=1.0, y2=0.7),   # E-W outgoing (right side)
    "ns_in": ROI(x1=0.3, y1=0.0, x2=0.7, y2=0.35),    # N-S incoming (top)
    "ns_out": ROI(x1=0.3, y1=0.65, x2=0.7, y2=1.0),   # N-S outgoing (bottom)
}


def create_roi_mask(roi: ROI, width: int, height: int) -> np.ndarray:
    """
    Create a binary mask for the given ROI.

    Returns:
        numpy array of shape (height, width) with 1s inside ROI and 0s outside.
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    px1, py1, px2, py2 = roi.to_pixels(width, height)
    mask[py1:py2, px1:px2] = 1
    return mask


def apply_roi_mask(frame: np.ndarray, roi: ROI) -> np.ndarray:
    """
    Apply an ROI mask to a frame, zeroing out pixels outside the ROI.

    Args:
        frame: Input image (H, W, C) or (H, W).
        roi: ROI to apply.

    Returns:
        Masked frame with same shape as input.
    """
    height, width = frame.shape[:2]
    mask = create_roi_mask(roi, width, height)

    if len(frame.shape) == 3:
        mask = np.expand_dims(mask, axis=2)
        mask = np.repeat(mask, frame.shape[2], axis=2)

    return frame * mask


def count_detections_in_roi(
    detections: List[Tuple[float, float, float, float, float, int]],
    roi: ROI,
    frame_width: int,
    frame_height: int,
) -> int:
    """
    Count how many detection bounding-box centers fall within the ROI.

    Args:
        detections: List of (x1, y1, x2, y2, confidence, class_id) tuples.
        roi: ROI to check against.
        frame_width: Frame width in pixels.
        frame_height: Frame height in pixels.

    Returns:
        Count of detections whose center is inside the ROI.
    """
    count = 0
    for x1, y1, x2, y2, conf, cls in detections:
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        if roi.contains_point(center_x, center_y, frame_width, frame_height):
            count += 1
    return count


def estimate_queue_length(
    vehicle_count: int,
    calibration_ppm: float,
    avg_vehicle_length_px: float = 50.0,
) -> float:
    """
    Estimate queue length in meters from vehicle count and calibration.

    Args:
        vehicle_count: Number of vehicles in the queue.
        calibration_ppm: Pixels per meter calibration factor.
        avg_vehicle_length_px: Average vehicle length in pixels (default 50px).

    Returns:
        Estimated queue length in meters.
    """
    if calibration_ppm <= 0:
        logger.warning("Invalid calibration_ppm=%.2f — using default 10.0", calibration_ppm)
        calibration_ppm = 10.0

    queue_px = vehicle_count * avg_vehicle_length_px
    queue_meters = queue_px / calibration_ppm
    return round(queue_meters, 1)


def load_calibration(calibration_path: str) -> Optional[Dict]:
    """Load ROI calibration from a JSON file."""
    import json
    try:
        with open(calibration_path, "r") as f:
            data = json.load(f)
        logger.info("Loaded calibration from %s", calibration_path)
        return data
    except FileNotFoundError:
        logger.warning("Calibration file not found: %s — using defaults", calibration_path)
        return None
    except Exception as exc:
        logger.error("Failed to load calibration from %s: %s", calibration_path, exc)
        return None
