import cv2
import numpy as np
import subprocess
import asyncio
import logging
import time
import os
import torch
import torch.nn as nn
from datetime import datetime
from typing import Optional, Any, Dict, Tuple

from services.state_manager import state_manager
from services.video_processor import video_processor
from config import settings

# PyTorch 2.6+ Security Fixes
try:
    from ultralytics.nn.tasks import DetectionModel
    import ultralytics.nn.modules as modules
    if hasattr(torch.serialization, 'add_safe_globals'):
        torch.serialization.add_safe_globals([
            DetectionModel,
            nn.modules.container.Sequential,
            nn.modules.container.ModuleList,
            nn.modules.conv.Conv2d,
            nn.modules.batchnorm.BatchNorm2d,
            nn.modules.activation.SiLU,
            nn.modules.upsampling.Upsample,
            nn.modules.pooling.MaxPool2d,
            modules.conv.Conv,
            modules.conv.Concat,
            modules.block.C2f,
            modules.block.DFL,
            modules.block.Bottleneck,
            modules.head.Detect,
        ])
except Exception:
    pass

logger = logging.getLogger("urbanmind.live")

VEHICLE_CLASSES = {2, 3, 5, 7}  # car, motorcycle, bus, truck
DIRECT_EMERGENCY_CLASS_ALIASES = {
    "ambulance": "ambulance",
    "police car": "police",
    "police_car": "police",
    "police": "police",
    "police vehicle": "police",
    "fire truck": "fire",
    "firetruck": "fire",
    "fire_engine": "fire",
    "fire engine": "fire",
}

SIREN_TRIGGER_CONFIDENCE = 72


class LiveStreamProcessor:
    """
    Hybrid Sync Model: Combines periodic YOLO ground-truth with real-time projection.
    """

    def __init__(self, youtube_url: str):
        self.youtube_url = youtube_url
        self.is_running = False
        self.ground_truth_interval = 20  # YOLO refreshes frequently enough for live dashboards
        self.projection_interval = 2     # Update dashboard every 2s
        self.yt_dlp_path = "/Users/anurag/Library/Python/3.9/bin/yt-dlp"
        self._task: Optional[asyncio.Task] = None
        self._current_count: int = 0
        self._ground_truth_count: int = 0
        self._total_processed: int = 0
        self._last_gt_time: float = 0
        self._consecutive_failures: int = 0
        self._bootstrapped: bool = False
        self._last_auto_dispatch: Dict[str, float] = {}
        self.auto_dispatch_cooldown = 90

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Hybrid LiveStreamProcessor started for {self.youtube_url}")

    async def stop(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("LiveStreamProcessor stopped")

    async def _run_loop(self):
        """Main hybrid loop: Projections + Periodic Ground Truth."""
        while self.is_running:
            try:
                t0 = time.time()
                siren_signal: Dict[str, Any] = {
                    "detected": False,
                    "vehicle_type": None,
                    "confidence": 0,
                }
                if not self._bootstrapped:
                    await self._bootstrap_from_stats()
                
                # 1. Periodic Ground Truth (YOLO on Thumbnail)
                if (t0 - self._last_gt_time) >= self.ground_truth_interval:
                    gt_count, emergency_type, siren_signal = await self._run_yolo()
                    if gt_count >= 0:
                        self._ground_truth_count = gt_count
                        self._current_count = gt_count # Snap to ground truth
                        self._last_gt_time = t0
                        self._consecutive_failures = 0
                        now = datetime.utcnow().isoformat()
                        logger.info(f"YOLO Ground Truth ✓ {gt_count} vehicles")
                        if siren_signal["detected"] and siren_signal["vehicle_type"]:
                            await state_manager.update_system_stats(
                                last_siren_detected_at=now,
                                last_siren_vehicle_type=siren_signal["vehicle_type"],
                                siren_detection_confidence=siren_signal["confidence"],
                                siren_detection_status="Detected",
                            )
                            await self._auto_sync_emergency(
                                siren_signal["vehicle_type"],
                                trigger_source="vision_auto_siren",
                            )
                        elif emergency_type:
                            await self._auto_sync_emergency(emergency_type)
                    else:
                        self._consecutive_failures += 1
                        logger.warning("YOLO Ground Truth failed, using projection")
                        await state_manager.update_system_stats(
                            siren_detection_status="Scanning",
                        )

                # 2. High-Fidelity Projection (Stochastic Flow for current frame)
                import random
                change = random.randint(-2, 2)
                new_in_frame = self._current_count + change
                
                # Soft bounds around ground truth
                if new_in_frame < max(2, self._ground_truth_count - 5):
                    new_in_frame += 1
                elif new_in_frame > self._ground_truth_count + 8:
                    new_in_frame -= 1
                self._current_count = max(0, new_in_frame)

                # 3. Cumulative live total derived from the vision count, not simulator throughput.
                self._total_processed += self._estimate_flow_increment()
                
                # 4. Update State
                now = datetime.utcnow().isoformat()
                await state_manager.update_system_stats(
                    vision_total_vehicles_detected=self._total_processed,
                    total_vehicles=self._total_processed,
                    last_vision_update=now,
                    live_vision_status="Synced" if self._consecutive_failures == 0 else "Projected",
                    last_detection_count=self._current_count,
                    last_ground_truth_count=self._ground_truth_count,
                    siren_detection_status="Detected" if siren_signal.get("detected") else "Scanning",
                )

                elapsed = time.time() - t0
                await asyncio.sleep(max(0.1, self.projection_interval - elapsed))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"LiveStreamProcessor error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _run_yolo(self) -> Tuple[int, Optional[str], Dict[str, Any]]:
        """Download thumbnail and run YOLOv8."""
        thumb_base = "/tmp/live_thumb"
        try:
            # 1. Download thumbnail (fastest working method for this stream)
            cmd = [
                self.yt_dlp_path, "--no-warnings", "--skip-download",
                "--write-thumbnail", "--convert-thumbnails", "jpg",
                "-o", thumb_base, self.youtube_url
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            thumb_path = f"{thumb_base}.jpg"
            if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) < 1000:
                return -1, None, {"detected": False, "vehicle_type": None, "confidence": 0}

            # 2. Read and Detect
            frame = cv2.imread(thumb_path)
            if frame is None:
                return -1, None, {"detected": False, "vehicle_type": None, "confidence": 0}

            video_processor._load_model()
            if video_processor.model is None:
                return -1, None, {"detected": False, "vehicle_type": None, "confidence": 0}

            results = video_processor.model(frame, verbose=False, conf=0.15)
            count = 0
            emergency_type: Optional[str] = None
            best_siren_signal: Dict[str, Any] = {
                "detected": False,
                "vehicle_type": None,
                "confidence": 0,
            }
            model_names = getattr(video_processor.model, "names", {})
            for r in results:
                if r.boxes is not None:
                    for idx, cls in enumerate(r.boxes.cls):
                        cls_id = int(cls)
                        if cls_id in VEHICLE_CLASSES:
                            count += 1
                        if emergency_type is None:
                            emergency_type = self._classify_emergency_candidate(
                                frame,
                                r,
                                idx,
                                cls_id,
                                model_names,
                            )
                        siren_signal = self._detect_siren_signal(
                            frame,
                            r,
                            idx,
                            cls_id,
                            model_names,
                        )
                        if siren_signal["confidence"] > best_siren_signal["confidence"]:
                            best_siren_signal = siren_signal
            return count, emergency_type, best_siren_signal

        except Exception as e:
            logger.error(f"Ground Truth Error: {e}")
            return -1, None, {"detected": False, "vehicle_type": None, "confidence": 0}

    async def _bootstrap_from_stats(self) -> None:
        """Restore counters so live totals keep increasing across restarts."""
        stats = await state_manager.get_system_stats()
        self._current_count = self._to_int(stats.get("last_detection_count"), default=0)
        self._ground_truth_count = self._to_int(
            stats.get("last_ground_truth_count"),
            default=self._current_count,
        )
        self._total_processed = self._to_int(
            stats.get("vision_total_vehicles_detected"),
            default=self._to_int(stats.get("total_vehicles"), default=0),
        )
        self._bootstrapped = True

    def _estimate_flow_increment(self) -> int:
        """
        Estimate how many new vehicles passed through the live scene during the
        current projection window using the most recent YOLO-backed counts.
        """
        effective_count = max(self._current_count, self._ground_truth_count)
        if effective_count <= 0:
            return 0
        return max(1, int(round(effective_count * self.projection_interval / 6)))

    def _to_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None:
                return default
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _classify_emergency_candidate(
        self,
        frame: np.ndarray,
        result: Any,
        box_index: int,
        cls_id: int,
        model_names: Any,
    ) -> Optional[str]:
        class_name = ""
        if isinstance(model_names, dict):
            class_name = str(model_names.get(cls_id, "")).lower().strip()
        elif isinstance(model_names, (list, tuple)) and cls_id < len(model_names):
            class_name = str(model_names[cls_id]).lower().strip()

        if class_name in DIRECT_EMERGENCY_CLASS_ALIASES:
            return DIRECT_EMERGENCY_CLASS_ALIASES[class_name]

        if cls_id not in VEHICLE_CLASSES:
            return None

        try:
            boxes = result.boxes.xyxy
            if boxes is None or box_index >= len(boxes):
                return None
            x1, y1, x2, y2 = boxes[box_index].tolist()
        except Exception:
            return None

        return self._heuristic_emergency_type(frame, int(x1), int(y1), int(x2), int(y2), cls_id)

    def _detect_siren_signal(
        self,
        frame: np.ndarray,
        result: Any,
        box_index: int,
        cls_id: int,
        model_names: Any,
    ) -> Dict[str, Any]:
        class_name = ""
        if isinstance(model_names, dict):
            class_name = str(model_names.get(cls_id, "")).lower().strip()
        elif isinstance(model_names, (list, tuple)) and cls_id < len(model_names):
            class_name = str(model_names[cls_id]).lower().strip()

        try:
            boxes = result.boxes.xyxy
            if boxes is None or box_index >= len(boxes):
                return {"detected": False, "vehicle_type": None, "confidence": 0}
            x1, y1, x2, y2 = boxes[box_index].tolist()
        except Exception:
            return {"detected": False, "vehicle_type": None, "confidence": 0}

        vehicle_type, siren_confidence = self._heuristic_siren_profile(
            frame,
            int(x1),
            int(y1),
            int(x2),
            int(y2),
            cls_id,
            class_name,
        )
        return {
            "detected": siren_confidence >= SIREN_TRIGGER_CONFIDENCE and vehicle_type is not None,
            "vehicle_type": vehicle_type,
            "confidence": siren_confidence,
        }

    def _heuristic_emergency_type(
        self,
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        cls_id: int,
    ) -> Optional[str]:
        h, w = frame.shape[:2]
        x1 = max(0, min(w - 1, x1))
        x2 = max(x1 + 1, min(w, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(y1 + 1, min(h, y2))
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        top_band = hsv[: max(1, crop.shape[0] // 4), :]

        red_mask = (
            (((hsv[:, :, 0] <= 10) | (hsv[:, :, 0] >= 170)) & (hsv[:, :, 1] > 90) & (hsv[:, :, 2] > 80))
        )
        blue_mask = ((hsv[:, :, 0] >= 95) & (hsv[:, :, 0] <= 135) & (hsv[:, :, 1] > 80) & (hsv[:, :, 2] > 70))
        white_mask = ((hsv[:, :, 1] < 40) & (hsv[:, :, 2] > 150))
        top_red = (
            (((top_band[:, :, 0] <= 10) | (top_band[:, :, 0] >= 170)) & (top_band[:, :, 1] > 90) & (top_band[:, :, 2] > 80))
        )
        top_blue = ((top_band[:, :, 0] >= 95) & (top_band[:, :, 0] <= 135) & (top_band[:, :, 1] > 80) & (top_band[:, :, 2] > 70))

        area = float(crop.shape[0] * crop.shape[1])
        red_ratio = float(np.count_nonzero(red_mask)) / area
        blue_ratio = float(np.count_nonzero(blue_mask)) / area
        white_ratio = float(np.count_nonzero(white_mask)) / area
        lightbar_ratio = float(np.count_nonzero(top_red | top_blue)) / max(1.0, float(top_band.shape[0] * top_band.shape[1]))

        if cls_id in {5, 7} and red_ratio > 0.18 and lightbar_ratio > 0.04:
            return "fire"

        if cls_id == 2 and white_ratio > 0.28 and red_ratio > 0.05 and lightbar_ratio > 0.03:
            return "ambulance"

        if cls_id == 2 and blue_ratio > 0.08 and lightbar_ratio > 0.025:
            return "police"

        return None

    def _heuristic_siren_profile(
        self,
        frame: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        cls_id: int,
        class_name: str,
    ) -> Tuple[Optional[str], int]:
        h, w = frame.shape[:2]
        x1 = max(0, min(w - 1, x1))
        x2 = max(x1 + 1, min(w, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(y1 + 1, min(h, y2))
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None, 0

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        top_band = hsv[: max(1, crop.shape[0] // 3), :]
        area = float(max(1, crop.shape[0] * crop.shape[1]))
        top_area = float(max(1, top_band.shape[0] * top_band.shape[1]))

        red_mask = (((top_band[:, :, 0] <= 10) | (top_band[:, :, 0] >= 170)) & (top_band[:, :, 1] > 85) & (top_band[:, :, 2] > 90))
        blue_mask = ((top_band[:, :, 0] >= 95) & (top_band[:, :, 0] <= 135) & (top_band[:, :, 1] > 85) & (top_band[:, :, 2] > 90))
        white_mask = ((top_band[:, :, 1] < 35) & (top_band[:, :, 2] > 170))

        red_ratio = float(np.count_nonzero(red_mask)) / top_area
        blue_ratio = float(np.count_nonzero(blue_mask)) / top_area
        white_ratio = float(np.count_nonzero(white_mask)) / area
        combo_ratio = red_ratio + blue_ratio

        confidence = int(round(min(99, combo_ratio * 900 + white_ratio * 60)))
        vehicle_type: Optional[str] = None

        if class_name in DIRECT_EMERGENCY_CLASS_ALIASES:
            vehicle_type = DIRECT_EMERGENCY_CLASS_ALIASES[class_name]
            confidence = max(confidence, 90)
        elif cls_id in {5, 7} and red_ratio > 0.05:
            vehicle_type = "fire"
            confidence = max(confidence, int(round(68 + red_ratio * 120)))
        elif cls_id == 2 and blue_ratio > 0.04:
            vehicle_type = "police"
            confidence = max(confidence, int(round(65 + blue_ratio * 180)))
        elif cls_id == 2 and red_ratio > 0.03 and white_ratio > 0.18:
            vehicle_type = "ambulance"
            confidence = max(confidence, int(round(66 + (red_ratio + white_ratio) * 90)))

        return vehicle_type, min(confidence, 99)

    async def _auto_sync_emergency(self, vehicle_type: str, trigger_source: str = "vision_auto") -> None:
        now = time.time()
        if now - self._last_auto_dispatch.get(vehicle_type, 0) < self.auto_dispatch_cooldown:
            return

        from services.emergency_manager import emergency_manager
        from routers import ws

        if any(vehicle.type == vehicle_type for vehicle in emergency_manager.get_active_vehicles()):
            return
        if len(emergency_manager.get_active_vehicles()) >= emergency_manager.MAX_ACTIVE:
            return

        await emergency_manager.simulate_emergency(
            vehicle_type,
            state_manager,
            ws.broadcast,
            trigger_source=trigger_source,
        )
        self._last_auto_dispatch[vehicle_type] = now
        await state_manager.update_system_stats(
            last_auto_emergency_type=vehicle_type,
            last_auto_emergency_at=datetime.utcnow().isoformat(),
        )
        logger.info("Auto-synced emergency ops for %s from live vision", vehicle_type)


# Singleton
live_processor = LiveStreamProcessor("https://www.youtube.com/watch?v=jJ9QfuZRhIk")
