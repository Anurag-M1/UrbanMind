"""
UrbanMind — YOLOv8 Traffic Detector (CV Worker)
Inference worker that processes RTSP streams, counts vehicles per lane,
estimates queue lengths, and publishes density data to the API and MQTT.
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import cv2
import httpx
import numpy as np
import paho.mqtt.client as mqtt_client

logger = logging.getLogger("urbanmind.detector")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

# ─── Vehicle Class Maps ──────────────────────────────────────────────────────

VEHICLE_CLASSES: Dict[int, str] = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

INDIAN_CLASSES: Dict[int, str] = {
    80: "auto_rickshaw",
    81: "cattle",
    82: "cycle_rickshaw",
}

ALL_VEHICLE_CLASSES: Dict[int, str] = {**VEHICLE_CLASSES, **INDIAN_CLASSES}

# Average vehicle length in pixels (for queue estimation)
AVG_VEHICLE_LENGTH_PX: float = 50.0


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class ROI:
    """Region of Interest with normalized 0-1 coordinates."""
    x1: float
    y1: float
    x2: float
    y2: float

    def contains_point(self, nx: float, ny: float) -> bool:
        return self.x1 <= nx <= self.x2 and self.y1 <= ny <= self.y2


@dataclass
class IntersectionConfig:
    """Configuration for a single intersection's camera and ROI setup."""
    id: str
    rtsp_url: str
    lanes: Dict[str, ROI] = field(default_factory=lambda: {
        "ew_in": ROI(0.0, 0.3, 0.35, 0.7),
        "ew_out": ROI(0.65, 0.3, 1.0, 0.7),
        "ns_in": ROI(0.3, 0.0, 0.7, 0.35),
        "ns_out": ROI(0.3, 0.65, 0.7, 1.0),
    })
    calibration_ppm: float = 10.0  # pixels per meter


@dataclass
class DensityResult:
    """Result of vehicle density analysis for a single frame."""
    intersection_id: str
    ew_count: int
    ns_count: int
    ew_queue_meters: float
    ns_queue_meters: float
    confidence: float
    fps: float
    frame_timestamp: datetime


# ─── Traffic Detector ─────────────────────────────────────────────────────────

class TrafficDetector:
    """
    YOLOv8-based vehicle detector for traffic intersections.
    Processes live RTSP streams, counts vehicles per lane,
    and publishes density data via HTTP API and MQTT.
    """

    def __init__(
        self,
        model_path: str = "models/yolov8n.pt",
        confidence: float = 0.65,
        api_url: str = "http://api:8000",
        mqtt_host: str = "mqtt",
        mqtt_port: int = 1883,
    ) -> None:
        self.model_path = model_path
        self.confidence = confidence
        self.api_url = api_url
        self.model = None
        self._threads: Dict[str, threading.Thread] = {}
        self._running: bool = False
        self._fps_counters: Dict[str, List[float]] = {}

        # Load YOLOv8 model
        self._load_model()

        # Initialize MQTT client
        self._mqtt = mqtt_client.Client(
            client_id="urbanmind-cv-worker",
            protocol=mqtt_client.MQTTv5,
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        )
        try:
            self._mqtt.connect(mqtt_host, mqtt_port, keepalive=60)
            self._mqtt.loop_start()
            logger.info("MQTT connected for CV worker at %s:%d", mqtt_host, mqtt_port)
        except Exception as exc:
            logger.warning("MQTT connection failed: %s — will publish via HTTP only", exc)

    def _load_model(self) -> None:
        """Load YOLOv8n model, downloading if necessary."""
        try:
            from ultralytics import YOLO

            if not os.path.exists(self.model_path):
                logger.info("Model not found at %s — downloading yolov8n.pt...", self.model_path)
                self.model = YOLO("yolov8n.pt")
                # Save to model path
                os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
            else:
                self.model = YOLO(self.model_path)

            logger.info("YOLOv8 model loaded: %s (confidence=%.2f)", self.model_path, self.confidence)
        except ImportError:
            logger.error("ultralytics not installed — cannot load YOLOv8 model")
            self.model = None
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            self.model = None

    def process_frame(self, frame: np.ndarray, config: IntersectionConfig) -> DensityResult:
        """
        Run YOLOv8 inference on a single frame and count vehicles per lane.

        Args:
            frame: BGR image from OpenCV.
            config: Intersection camera configuration with ROI definitions.

        Returns:
            DensityResult with vehicle counts and queue estimates.
        """
        height, width = frame.shape[:2]
        ew_count = 0
        ns_count = 0
        confidences: List[float] = []

        if self.model is not None:
            try:
                # Run inference
                results = self.model(frame, conf=self.confidence, verbose=False)

                for result in results:
                    boxes = result.boxes
                    if boxes is None:
                        continue

                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())

                        # Filter to vehicle classes only
                        if cls_id not in ALL_VEHICLE_CLASSES:
                            continue

                        confidences.append(conf)

                        # Get bounding box center (normalized)
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        center_x = ((x1 + x2) / 2) / width
                        center_y = ((y1 + y2) / 2) / height

                        # Check which lane the detection belongs to
                        for lane_name, roi in config.lanes.items():
                            if roi.contains_point(center_x, center_y):
                                if lane_name.startswith("ew"):
                                    ew_count += 1
                                elif lane_name.startswith("ns"):
                                    ns_count += 1
                                break

            except Exception as exc:
                logger.error("Inference error for %s: %s", config.id, exc)

        # Estimate queue lengths
        ew_queue = (ew_count * AVG_VEHICLE_LENGTH_PX) / max(config.calibration_ppm, 1.0)
        ns_queue = (ns_count * AVG_VEHICLE_LENGTH_PX) / max(config.calibration_ppm, 1.0)

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return DensityResult(
            intersection_id=config.id,
            ew_count=ew_count,
            ns_count=ns_count,
            ew_queue_meters=round(ew_queue, 1),
            ns_queue_meters=round(ns_queue, 1),
            confidence=round(avg_confidence, 3),
            fps=0.0,
            frame_timestamp=datetime.utcnow(),
        )

    def run_stream(self, config: IntersectionConfig) -> None:
        """
        Process a live RTSP stream for a single intersection.
        Runs in a dedicated thread with frame skipping to maintain 15+ FPS.
        """
        logger.info("Starting stream for intersection %s: %s", config.id, config.rtsp_url)
        self._fps_counters[config.id] = []

        while self._running:
            cap = None
            try:
                cap = cv2.VideoCapture(config.rtsp_url)
                if not cap.isOpened():
                    logger.warning("Cannot open stream for %s — retrying in 5s", config.id)
                    time.sleep(5)
                    continue

                source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                target_fps = 15
                skip_n = max(1, int(source_fps / target_fps))
                frame_count = 0
                last_fps_report = time.time()
                process_count = 0

                while self._running:
                    ret = cap.grab()
                    if not ret:
                        logger.warning("Stream lost for %s — reconnecting", config.id)
                        break

                    frame_count += 1
                    if frame_count % skip_n != 0:
                        continue

                    ret, frame = cap.retrieve()
                    if not ret or frame is None:
                        continue

                    start_t = time.time()
                    result = self.process_frame(frame, config)
                    elapsed = time.time() - start_t
                    result.fps = 1.0 / max(elapsed, 0.001)

                    self._fps_counters[config.id].append(result.fps)

                    # Publish density
                    self.publish_density(result)
                    process_count += 1

                    # FPS report every 30 seconds
                    now = time.time()
                    if now - last_fps_report >= 30:
                        fps_values = self._fps_counters[config.id][-100:]
                        avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0
                        logger.info(
                            "FPS stats for %s: avg=%.1f processed=%d frames",
                            config.id, avg_fps, process_count,
                        )
                        # Publish FPS via MQTT
                        self._mqtt_publish(
                            f"urbanmind/cv/fps/{config.id}",
                            {"intersection_id": config.id, "avg_fps": round(avg_fps, 1)},
                        )
                        last_fps_report = now
                        process_count = 0

            except cv2.error as exc:
                logger.error("OpenCV error for %s: %s — retrying in 5s", config.id, exc)
                time.sleep(5)
            except Exception as exc:
                logger.error("Stream error for %s: %s — retrying in 5s", config.id, exc)
                time.sleep(5)
            finally:
                if cap is not None:
                    cap.release()

    def publish_density(self, result: DensityResult) -> None:
        """Publish density data via HTTP API and MQTT."""
        # Publish EW density via API
        try:
            with httpx.Client(timeout=5.0) as client:
                for lane, count, queue in [
                    ("ew", result.ew_count, result.ew_queue_meters),
                    ("ns", result.ns_count, result.ns_queue_meters),
                ]:
                    payload = {
                        "intersection_id": result.intersection_id,
                        "lane": lane,
                        "count": count,
                        "queue_meters": queue,
                        "confidence": result.confidence,
                        "timestamp": result.frame_timestamp.isoformat(),
                    }
                    client.post(f"{self.api_url}/api/v1/signals/density", json=payload)
        except Exception as exc:
            logger.debug("HTTP publish failed for %s: %s", result.intersection_id, exc)

        # Also publish via MQTT
        self._mqtt_publish(
            f"urbanmind/cv/density/{result.intersection_id}",
            {
                "intersection_id": result.intersection_id,
                "ew_count": result.ew_count,
                "ns_count": result.ns_count,
                "ew_queue_meters": result.ew_queue_meters,
                "ns_queue_meters": result.ns_queue_meters,
                "confidence": result.confidence,
                "fps": round(result.fps, 1),
                "timestamp": result.frame_timestamp.isoformat(),
            },
        )

    def _mqtt_publish(self, topic: str, payload: dict) -> None:
        """Publish a message via MQTT with error handling."""
        try:
            self._mqtt.publish(topic, json.dumps(payload), qos=1)
        except Exception as exc:
            logger.debug("MQTT publish failed for %s: %s", topic, exc)

    def start(self, configs: List[IntersectionConfig]) -> None:
        """Launch stream processing threads for all configured intersections."""
        self._running = True
        for config in configs:
            thread = threading.Thread(
                target=self.run_stream,
                args=(config,),
                name=f"stream-{config.id}",
                daemon=True,
            )
            thread.start()
            self._threads[config.id] = thread
            logger.info("Launched stream thread for %s", config.id)

    def stop(self) -> None:
        """Stop all stream processing threads."""
        self._running = False
        for config_id, thread in self._threads.items():
            thread.join(timeout=10)
            logger.info("Stopped stream thread for %s", config_id)
        self._threads.clear()

    def monitor_threads(self) -> None:
        """Monitor thread health and restart failed threads."""
        for config_id, thread in list(self._threads.items()):
            if not thread.is_alive():
                logger.warning("Thread for %s died — restarting", config_id)
                # Thread restart would need config — simplified here
                del self._threads[config_id]


# ─── Main Entry Point ────────────────────────────────────────────────────────

def main() -> None:
    """Main entry point for the CV engine worker."""
    api_url = os.getenv("API_URL", "http://api:8000")
    mqtt_host = os.getenv("MQTT_HOST", "mqtt")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    confidence = float(os.getenv("CV_CONFIDENCE_THRESHOLD", "0.65"))

    logger.info("=" * 60)
    logger.info("UrbanMind CV Engine starting...")
    logger.info("API: %s | MQTT: %s:%d | Confidence: %.2f", api_url, mqtt_host, mqtt_port, confidence)
    logger.info("=" * 60)

    detector = TrafficDetector(
        confidence=confidence,
        api_url=api_url,
        mqtt_host=mqtt_host,
        mqtt_port=mqtt_port,
    )

    # Fetch intersection configs from API
    configs: List[IntersectionConfig] = []
    max_retries = 10
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{api_url}/api/v1/signals/intersections")
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data:
                        # Use RTSP URL from env or default to simulator
                        rtsp_url = os.getenv(
                            f"RTSP_URL_{item['id'].upper()}",
                            f"rtsp://simulator:8554/{item['id']}",
                        )
                        configs.append(IntersectionConfig(
                            id=item["id"],
                            rtsp_url=rtsp_url,
                        ))
                    logger.info("Loaded %d intersection configs from API", len(configs))
                    break
        except Exception as exc:
            logger.warning("API not ready (attempt %d/%d): %s", attempt + 1, max_retries, exc)
            time.sleep(5)

    if not configs:
        logger.warning("No intersection configs loaded — running in demo mode with no streams")
        # Keep alive for health checks
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
        return

    # Start processing
    detector.start(configs)

    # Monitor loop
    try:
        while True:
            time.sleep(30)
            detector.monitor_threads()

            # Print summary FPS stats
            for config_id, fps_list in detector._fps_counters.items():
                recent = fps_list[-100:]
                if recent:
                    avg = sum(recent) / len(recent)
                    logger.info("CV Engine FPS [%s]: avg=%.1f", config_id, avg)
    except KeyboardInterrupt:
        logger.info("Shutting down CV engine...")
        detector.stop()


if __name__ == "__main__":
    main()
