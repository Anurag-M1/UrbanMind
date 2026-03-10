from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from edge.config import EdgeConfig, configure_logging, load_config

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover - optional dependency
    YOLO = None


LOGGER = configure_logging(__name__)
ALLOWED_CLASSES = {"car", "motorcycle", "bus", "truck", "person"}


@dataclass(slots=True)
class Detection:
    """Represents an object detection for one video frame."""

    class_name: str
    bbox: tuple[int, int, int, int]
    confidence: float
    lane_id: str


class YoloVehicleDetector:
    """Runs YOLOv8 inference on an RTSP stream."""

    def __init__(self, config: EdgeConfig) -> None:
        """Initializes the detector.

        Args:
            config: Edge runtime configuration.

        Returns:
            None.
        """

        self.config = config
        self.model = self._load_model()

    def _load_model(self) -> YOLO | None:
        """Loads the YOLO model if the dependency is available.

        Args:
            None.

        Returns:
            A YOLO model instance or None.
        """

        if YOLO is None:
            LOGGER.warning("ultralytics not installed; detector will emit empty frames")
            return None
        model_path = self.config.yolo_model_path or "yolov8n.pt"
        return YOLO(model_path if Path(model_path).exists() else "yolov8n.pt")

    def _assign_lane_id(self, bbox: tuple[int, int, int, int], frame_width: int) -> str:
        """Assigns a lane id by splitting the frame into vertical zones.

        Args:
            bbox: Detection bounding box as x1, y1, x2, y2.
            frame_width: Width of the frame in pixels.

        Returns:
            Lane identifier string.
        """

        center_x = (bbox[0] + bbox[2]) / 2
        zone_width = max(1, frame_width / max(1, self.config.lane_count))
        zone_index = min(self.config.lane_count - 1, int(center_x // zone_width))
        return f"lane_{zone_index + 1}"

    def _maybe_draw(self, frame: object, detections: list[Detection]) -> None:
        """Draws debug bounding boxes when enabled.

        Args:
            frame: Mutable image frame.
            detections: Detections to render.

        Returns:
            None.
        """

        if not self.config.debug or cv2 is None:
            return
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 194, 203), 2)
            cv2.putText(
                frame,
                f"{detection.class_name}:{detection.confidence:.2f} {detection.lane_id}",
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

    def process_frame(self, frame: object) -> list[Detection]:
        """Runs object detection on a single frame.

        Args:
            frame: OpenCV image frame.

        Returns:
            List of lane-tagged detections.
        """

        if self.model is None or cv2 is None:
            return []
        results = self.model.predict(frame, verbose=False, conf=self.config.confidence_threshold)
        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                confidence = float(box.conf[0])
                class_name = result.names[int(box.cls[0])]
                if class_name not in ALLOWED_CLASSES or confidence < self.config.confidence_threshold:
                    continue
                x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
                lane_id = self._assign_lane_id((x1, y1, x2, y2), frame.shape[1])
                detections.append(
                    Detection(
                        class_name=class_name,
                        bbox=(x1, y1, x2, y2),
                        confidence=confidence,
                        lane_id=lane_id,
                    )
                )
        self._maybe_draw(frame, detections)
        return detections

    def stream(self, max_frames: int | None = None) -> Iterator[list[Detection]]:
        """Streams detections from an RTSP camera at the configured target FPS.

        Args:
            max_frames: Optional frame cap for testing.

        Returns:
            An iterator of detections for each processed frame.
        """

        if cv2 is None:
            LOGGER.warning("opencv not installed; stream will produce no frames")
            return iter(())
        capture = cv2.VideoCapture(self.config.rtsp_stream_url)
        if not capture.isOpened():
            LOGGER.warning("unable to open RTSP stream %s", self.config.rtsp_stream_url)
            return iter(())

        processed = 0
        next_frame_due = time.monotonic()
        while capture.isOpened():
            ok, frame = capture.read()
            if not ok:
                break
            now = time.monotonic()
            if now < next_frame_due:
                continue
            next_frame_due = now + (1 / max(1, self.config.target_fps))
            yield self.process_frame(frame)
            processed += 1
            if max_frames is not None and processed >= max_frames:
                break
        capture.release()


def main() -> None:
    """Runs a short detector smoke test.

    Args:
        None.

    Returns:
        None.
    """

    detector = YoloVehicleDetector(load_config())
    for index, detections in enumerate(detector.stream(max_frames=3), start=1):
        LOGGER.info("frame=%s detections=%s", index, detections)


if __name__ == "__main__":
    main()
