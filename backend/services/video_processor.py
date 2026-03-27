import cv2
import numpy as np
import base64
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime

from models.intersection import VehicleDetection, VideoFrame, VideoAnalysisResult
from services.webster import calculate as webster_calculate
from config import settings

logger = logging.getLogger("urbanmind.video")

# Vehicle class mapping from COCO/YOLOv8
VEHICLE_CLASSES = {0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
VEHICLE_LABELS_DISPLAY = {
    2: "Car", 3: "Motorcycle/Bike", 5: "Bus",
    7: "Truck", 0: "Pedestrian", 1: "Bicycle",
}
# Colors for drawing (BGR for OpenCV)
CLASS_COLORS_BGR = {
    2: (255, 136, 68),    # Car: blue #4488FF -> BGR
    3: (0, 204, 255),     # Motorcycle: yellow #FFCC00 -> BGR
    5: (51, 136, 255),    # Bus: orange #FF8833 -> BGR
    7: (51, 136, 255),    # Truck: orange
    0: (255, 85, 170),    # Pedestrian: purple #AA55FF -> BGR
    1: (0, 204, 255),     # Bicycle: yellow
}


class VideoProcessor:
    def __init__(self) -> None:
        self.model: Any = None
        self.job_store: Dict[str, VideoAnalysisResult] = {}
        self._model_loaded = False

    def _load_model(self) -> None:
        """Load YOLOv8n model (downloads automatically if not present)."""
        if self._model_loaded:
            return
        try:
            import torch
            try:
                # Support for PyTorch 2.6+ security changes
                from ultralytics.nn.tasks import DetectionModel
                if hasattr(torch.serialization, 'add_safe_globals'):
                    torch.serialization.add_safe_globals([DetectionModel])
            except Exception as torch_e:
                logger.debug("Torch safe_globals setup skipped: %s", torch_e)

            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")
            self._model_loaded = True
            logger.info("YOLOv8n model loaded successfully")
        except Exception as e:
            logger.warning("YOLOv8 not available, using simulation mode: %s", e)
            self.model = None
            self._model_loaded = True

    async def analyze_video(
        self,
        video_path: str,
        video_id: str,
        intersection_id: str = "int_001",
        ws_broadcast: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> VideoAnalysisResult:
        """Full video analysis pipeline with YOLOv8 or simulated detection."""
        start_time = time.time()

        result = VideoAnalysisResult(
            video_id=video_id,
            filename=video_path.split("/")[-1],
            status="processing",
            intersections_detected=[intersection_id],
        )
        self.job_store[video_id] = result

        try:
            self._load_model()

            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                result.status = "error"
                result.error_message = "Could not open video file"
                return result

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0

            result.fps = fps
            result.total_frames = total_frames
            result.duration_seconds = round(duration, 2)

            # Sampling strategy: 5 frames/second, max 300
            sample_interval = max(1, int(fps / 5))
            max_processed = 300

            vehicle_counts: Dict[str, int] = {}
            lane_density: Dict[str, int] = {
                "ew_in": 0, "ew_out": 0, "ns_in": 0, "ns_out": 0, "intersection": 0
            }
            detection_frames: List[VideoFrame] = []
            all_ew_counts: List[int] = []
            all_ns_counts: List[int] = []

            frame_idx = 0
            processed_count = 0

            while True:
                ret, frame = cap.read()
                if not ret or processed_count >= max_processed:
                    break

                if frame_idx % sample_interval != 0:
                    frame_idx += 1
                    continue

                timestamp = frame_idx / fps if fps > 0 else 0
                detections: List[VehicleDetection] = []
                ew_count = 0
                ns_count = 0

                if self.model is not None:
                    # Real YOLOv8 inference
                    results = self.model(
                        frame,
                        conf=settings.CONFIDENCE_THRESHOLD,
                        iou=0.45,
                        verbose=False,
                    )
                    for r in results:
                        boxes = r.boxes
                        if boxes is None:
                            continue
                        for box in boxes:
                            cls_id = int(box.cls[0].item())
                            if cls_id not in VEHICLE_CLASSES:
                                continue
                            conf = float(box.conf[0].item())
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            # Normalize bbox
                            nx1 = x1 / width
                            ny1 = y1 / height
                            nx2 = x2 / width
                            ny2 = y2 / height
                            cx = (nx1 + nx2) / 2
                            cy = (ny1 + ny2) / 2

                            lane = self._assign_lane(cx, cy)
                            class_name = VEHICLE_CLASSES[cls_id]
                            display_name = VEHICLE_LABELS_DISPLAY.get(cls_id, class_name)

                            det = VehicleDetection(
                                frame_number=frame_idx,
                                class_name=display_name,
                                confidence=round(conf, 3),
                                bbox=[round(nx1, 4), round(ny1, 4), round(nx2, 4), round(ny2, 4)],
                                lane=lane,
                                intersection_id=intersection_id,
                            )
                            detections.append(det)

                            # Count by lane direction
                            vehicle_counts[display_name] = vehicle_counts.get(display_name, 0) + 1
                            lane_density[lane] = lane_density.get(lane, 0) + 1

                            if lane.startswith("ew"):
                                ew_count += 1
                            elif lane.startswith("ns"):
                                ns_count += 1
                else:
                    # Simulated detection for demo
                    sim_ew = np.random.randint(5, 18)
                    sim_ns = np.random.randint(3, 14)
                    ew_count = sim_ew
                    ns_count = sim_ns

                    for _ in range(sim_ew + sim_ns):
                        cls_id = np.random.choice([2, 2, 2, 3, 3, 5, 7, 0], p=[0.35, 0.15, 0.10, 0.12, 0.08, 0.08, 0.07, 0.05])
                        display_name = VEHICLE_LABELS_DISPLAY.get(int(cls_id), "Car")
                        cx = np.random.random()
                        cy = np.random.random()
                        bw = 0.04 + np.random.random() * 0.06
                        bh = 0.03 + np.random.random() * 0.05
                        lane = self._assign_lane(cx, cy)

                        det = VehicleDetection(
                            frame_number=frame_idx,
                            class_name=display_name,
                            confidence=round(0.65 + np.random.random() * 0.3, 3),
                            bbox=[
                                round(max(0, cx - bw / 2), 4),
                                round(max(0, cy - bh / 2), 4),
                                round(min(1, cx + bw / 2), 4),
                                round(min(1, cy + bh / 2), 4),
                            ],
                            lane=lane,
                            intersection_id=intersection_id,
                        )
                        detections.append(det)
                        vehicle_counts[display_name] = vehicle_counts.get(display_name, 0) + 1
                        lane_density[lane] = lane_density.get(lane, 0) + 1

                all_ew_counts.append(ew_count)
                all_ns_counts.append(ns_count)

                # Every 10th sampled frame: generate annotated image
                should_annotate = (processed_count % 10 == 0) and len(detection_frames) < 20
                annotated_b64 = ""
                if should_annotate:
                    annotated_b64 = self._annotate_frame(
                        frame, detections, ew_count, ns_count,
                        frame_idx, timestamp, width, height, intersection_id,
                    )

                video_frame = VideoFrame(
                    frame_number=frame_idx,
                    timestamp_seconds=round(timestamp, 2),
                    detections=detections,
                    ew_count=ew_count,
                    ns_count=ns_count,
                    annotated_image_b64=annotated_b64,
                )

                if should_annotate:
                    detection_frames.append(video_frame)

                processed_count += 1
                result.frames_processed = processed_count
                frame_idx += 1

                # Yield to event loop periodically
                if processed_count % 20 == 0:
                    await asyncio.sleep(0.01)

            cap.release()

            # Calculate recommended timings with Webster's formula
            avg_ew = int(np.mean(all_ew_counts)) if all_ew_counts else 10
            avg_ns = int(np.mean(all_ns_counts)) if all_ns_counts else 8
            recommended = webster_calculate(avg_ew, avg_ns)

            result.vehicle_counts = vehicle_counts
            result.lane_density = {k: v for k, v in lane_density.items() if v > 0}
            result.recommended_timings = recommended
            result.detection_frames = detection_frames
            result.processing_time_seconds = round(time.time() - start_time, 2)
            result.frames_processed = processed_count
            result.status = "complete"

            logger.info(
                "Video %s analyzed: %d frames, %d detections, %.1fs",
                video_id, processed_count, sum(vehicle_counts.values()),
                result.processing_time_seconds,
            )

            if ws_broadcast:
                await ws_broadcast({
                    "type": "video_analysis_complete",
                    "video_id": video_id,
                    "status": "complete",
                    "vehicle_counts": vehicle_counts,
                    "recommended_timings": recommended,
                })

            return result

        except asyncio.TimeoutError:
            result.status = "error"
            result.error_message = "Processing timed out (>120s)"
            result.processing_time_seconds = round(time.time() - start_time, 2)
            return result
        except Exception as e:
            logger.error("Video analysis error: %s", e)
            result.status = "error"
            result.error_message = str(e)
            result.processing_time_seconds = round(time.time() - start_time, 2)
            return result

    def get_job_status(self, video_id: str) -> Optional[VideoAnalysisResult]:
        return self.job_store.get(video_id)

    def _annotate_frame(
        self,
        frame: np.ndarray,
        detections: List[VehicleDetection],
        ew_count: int,
        ns_count: int,
        frame_num: int,
        timestamp: float,
        width: int,
        height: int,
        intersection_id: str,
    ) -> str:
        """Draw detection annotations on frame and return base64 JPEG."""
        annotated = frame.copy()

        # Draw lane zone overlays (semi-transparent)
        overlay = annotated.copy()
        # EW zones (top and bottom thirds) - blue tint
        cv2.rectangle(overlay, (0, 0), (width, height // 3), (180, 100, 50), -1)
        cv2.rectangle(overlay, (0, 2 * height // 3), (width, height), (180, 100, 50), -1)
        # NS zones (left and right thirds) - orange tint
        cv2.rectangle(overlay, (0, 0), (width // 3, height), (50, 100, 180), -1)
        cv2.rectangle(overlay, (2 * width // 3, 0), (width, height), (50, 100, 180), -1)
        cv2.addWeighted(overlay, 0.12, annotated, 0.88, 0, annotated)

        # Draw lane labels
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(annotated, "EW-IN", (width // 2 - 40, 25), font, 0.6, (255, 180, 80), 1)
        cv2.putText(annotated, "EW-OUT", (width // 2 - 50, height - 10), font, 0.6, (255, 180, 80), 1)
        cv2.putText(annotated, "NS-IN", (10, height // 2), font, 0.6, (80, 180, 255), 1)
        cv2.putText(annotated, "NS-OUT", (width - 90, height // 2), font, 0.6, (80, 180, 255), 1)

        # Draw bounding boxes
        for det in detections:
            x1 = int(det.bbox[0] * width)
            y1 = int(det.bbox[1] * height)
            x2 = int(det.bbox[2] * width)
            y2 = int(det.bbox[3] * height)

            # Get class color
            color = (255, 136, 68)  # default blue
            for cls_id, name in VEHICLE_LABELS_DISPLAY.items():
                if name == det.class_name:
                    color = CLASS_COLORS_BGR.get(cls_id, color)
                    break

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{det.class_name} {det.confidence:.0%}"
            label_size = cv2.getTextSize(label, font, 0.4, 1)[0]
            cv2.rectangle(
                annotated,
                (x1, y1 - label_size[1] - 6),
                (x1 + label_size[0] + 4, y1),
                color,
                -1,
            )
            cv2.putText(annotated, label, (x1 + 2, y1 - 4), font, 0.4, (0, 0, 0), 1)

        # Draw stats overlay
        stats_bg = np.zeros((60, 300, 3), dtype=np.uint8)
        stats_bg[:] = (20, 15, 10)
        cv2.addWeighted(
            annotated[5:65, 5:305], 0.3,
            stats_bg[:min(60, height - 5), :min(300, width - 5)], 0.7,
            0,
            annotated[5:65, 5:305],
        ) if height > 65 and width > 305 else None

        cv2.putText(
            annotated,
            f"EW: {ew_count}  NS: {ns_count}  Frame: {frame_num}",
            (12, 28),
            font, 0.6, (255, 255, 255), 1,
        )
        cv2.putText(
            annotated,
            f"{intersection_id} | t={timestamp:.1f}s",
            (12, 52),
            font, 0.5, (200, 200, 200), 1,
        )

        # Encode to JPEG base64
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, 75]
        _, buffer = cv2.imencode(".jpg", annotated, encode_params)
        return base64.b64encode(buffer).decode("utf-8")

    @staticmethod
    def _assign_lane(cx: float, cy: float) -> str:
        """Assign lane based on normalized center position."""
        if cy < 0.33:
            return "ew_in"
        elif cy > 0.67:
            return "ew_out"
        elif cx < 0.33:
            return "ns_in"
        elif cx > 0.67:
            return "ns_out"
        else:
            return "intersection"


video_processor = VideoProcessor()
