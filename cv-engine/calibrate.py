"""
UrbanMind — ROI Calibration Tool
Interactive tool for drawing lane ROI zones and measuring pixel-per-meter calibration.
"""

import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("urbanmind.calibrate")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")

# ─── State for mouse callbacks ────────────────────────────────────────────────

_drawing: bool = False
_roi_start: Optional[Tuple[int, int]] = None
_roi_end: Optional[Tuple[int, int]] = None
_current_roi: Optional[Tuple[int, int, int, int]] = None
_calibration_points: List[Tuple[int, int]] = []


def _mouse_callback(event: int, x: int, y: int, flags: int, param: dict) -> None:
    """Mouse callback for ROI drawing and calibration point selection."""
    global _drawing, _roi_start, _roi_end, _current_roi

    mode = param.get("mode", "roi")

    if mode == "roi":
        if event == cv2.EVENT_LBUTTONDOWN:
            _drawing = True
            _roi_start = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and _drawing:
            _roi_end = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            _drawing = False
            _roi_end = (x, y)
            if _roi_start is not None:
                _current_roi = (*_roi_start, x, y)
    elif mode == "calibrate":
        if event == cv2.EVENT_LBUTTONDOWN:
            _calibration_points.append((x, y))
            logger.info("Calibration point %d: (%d, %d)", len(_calibration_points), x, y)


def calibrate_intersection(
    source: str,
    intersection_id: str,
    output_dir: str = ".",
) -> None:
    """
    Interactive ROI calibration for an intersection camera.

    Steps:
    1. Open video source (RTSP URL or file path)
    2. Draw 4 ROI rectangles for EW_in, EW_out, NS_in, NS_out
    3. Click two points and enter known distance for ppm calibration
    4. Save calibration to JSON
    5. Preview detection with calibration

    Controls:
        - Click and drag to draw ROI
        - Press ENTER to confirm current ROI
        - Press 'c' to switch to calibration mode
        - Press 's' to save
        - Press 'q' to quit
    """
    global _current_roi, _calibration_points

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error("Cannot open video source: %s", source)
        return

    ret, frame = cap.read()
    if not ret:
        logger.error("Cannot read frame from: %s", source)
        cap.release()
        return

    height, width = frame.shape[:2]
    logger.info("Frame size: %dx%d", width, height)

    window_name = f"UrbanMind Calibration — {intersection_id}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    callback_params = {"mode": "roi"}
    cv2.setMouseCallback(window_name, _mouse_callback, callback_params)

    roi_names = ["ew_in", "ew_out", "ns_in", "ns_out"]
    rois: Dict[str, Dict[str, float]] = {}
    current_roi_idx = 0
    calibration_ppm = 10.0  # default

    logger.info("Draw ROI for '%s'. Click and drag, then press ENTER to confirm.", roi_names[0])

    while True:
        display = frame.copy()

        # Draw existing ROIs
        colors = {
            "ew_in": (0, 255, 0),
            "ew_out": (0, 200, 0),
            "ns_in": (255, 0, 0),
            "ns_out": (200, 0, 0),
        }
        for name, roi_data in rois.items():
            x1 = int(roi_data["x1"] * width)
            y1 = int(roi_data["y1"] * height)
            x2 = int(roi_data["x2"] * width)
            y2 = int(roi_data["y2"] * height)
            color = colors.get(name, (255, 255, 255))
            cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
            cv2.putText(display, name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw current ROI being drawn
        if _drawing and _roi_start is not None and _roi_end is not None:
            cv2.rectangle(display, _roi_start, _roi_end, (0, 255, 255), 2)

        # Draw calibration points
        for i, pt in enumerate(_calibration_points):
            cv2.circle(display, pt, 5, (0, 0, 255), -1)
            cv2.putText(display, str(i + 1), (pt[0] + 10, pt[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        if len(_calibration_points) == 2:
            cv2.line(display, _calibration_points[0], _calibration_points[1], (0, 0, 255), 2)

        # Instructions
        if current_roi_idx < len(roi_names):
            text = f"Draw ROI: {roi_names[current_roi_idx]} | ENTER=confirm | c=calibrate | s=save | q=quit"
        else:
            text = "All ROIs drawn | c=calibrate distance | s=save | q=quit"
        cv2.putText(display, text, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow(window_name, display)
        key = cv2.waitKey(30) & 0xFF

        if key == ord("q"):
            break
        elif key == 13:  # ENTER
            if _current_roi is not None and current_roi_idx < len(roi_names):
                x1, y1, x2, y2 = _current_roi
                rois[roi_names[current_roi_idx]] = {
                    "x1": min(x1, x2) / width,
                    "y1": min(y1, y2) / height,
                    "x2": max(x1, x2) / width,
                    "y2": max(y1, y2) / height,
                }
                logger.info("ROI '%s' confirmed: %s", roi_names[current_roi_idx], rois[roi_names[current_roi_idx]])
                current_roi_idx += 1
                _current_roi = None
                if current_roi_idx < len(roi_names):
                    logger.info("Now draw ROI for '%s'", roi_names[current_roi_idx])
                else:
                    logger.info("All ROIs drawn! Press 'c' for distance calibration or 's' to save.")
        elif key == ord("c"):
            callback_params["mode"] = "calibrate"
            _calibration_points.clear()
            logger.info("CALIBRATION MODE: Click two points with known real-world distance")
        elif key == ord("s"):
            # Calculate PPM if calibration points available
            if len(_calibration_points) == 2:
                p1, p2 = _calibration_points
                pixel_dist = np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
                try:
                    real_dist = float(input("Enter real-world distance in meters between the two points: "))
                    if real_dist > 0:
                        calibration_ppm = pixel_dist / real_dist
                        logger.info("Calibration: %.1f pixels / %.1f meters = %.2f PPM", pixel_dist, real_dist, calibration_ppm)
                except (ValueError, EOFError):
                    logger.warning("Invalid distance input — using default PPM")

            # Save calibration
            calibration = {
                "intersection_id": intersection_id,
                "width": width,
                "height": height,
                "rois": rois,
                "calibration_ppm": calibration_ppm,
            }
            output_path = os.path.join(output_dir, f"calibration_{intersection_id}.json")
            with open(output_path, "w") as f:
                json.dump(calibration, f, indent=2)
            logger.info("Calibration saved to: %s", output_path)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="UrbanMind ROI Calibration Tool")
    parser.add_argument("source", help="RTSP URL or video file path")
    parser.add_argument("--id", required=True, help="Intersection ID")
    parser.add_argument("--output", default=".", help="Output directory")
    args = parser.parse_args()

    calibrate_intersection(args.source, args.id, args.output)
