"""
UrbanMind — RTSP Stream Parser
OpenCV-based RTSP stream reader with reconnection logic and frame skipping.
"""

import logging
import time
from typing import Generator, Optional

import cv2
import numpy as np

logger = logging.getLogger("urbanmind.rtsp_parser")


class RTSPStream:
    """
    Opens and maintains an RTSP video stream with automatic reconnection.
    Yields frames at regular intervals, skipping to maintain target FPS.
    """

    def __init__(
        self,
        url: str,
        target_fps: int = 15,
        reconnect_delay: float = 5.0,
        max_retries: int = -1,
    ) -> None:
        self.url = url
        self.target_fps = target_fps
        self.reconnect_delay = reconnect_delay
        self.max_retries = max_retries  # -1 = infinite
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_count: int = 0
        self._source_fps: float = 30.0
        self._skip_n: int = 1
        self._running: bool = False
        logger.info("RTSPStream initialized: url=%s target_fps=%d", url, target_fps)

    def open(self) -> bool:
        """Open the RTSP stream."""
        try:
            self._cap = cv2.VideoCapture(self.url)
            if not self._cap.isOpened():
                logger.error("Failed to open RTSP stream: %s", self.url)
                return False

            self._source_fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
            # Calculate frame skip to achieve target FPS
            self._skip_n = max(1, int(self._source_fps / self.target_fps))
            self._frame_count = 0
            self._running = True

            logger.info(
                "RTSP stream opened: %s (source_fps=%.1f skip=%d → effective_fps=%.1f)",
                self.url, self._source_fps, self._skip_n, self._source_fps / self._skip_n,
            )
            return True

        except Exception as exc:
            logger.error("Failed to open RTSP stream %s: %s", self.url, exc)
            return False

    def read_frame(self) -> Optional[np.ndarray]:
        """Read the next frame from the stream, skipping frames as needed."""
        if self._cap is None or not self._cap.isOpened():
            return None

        try:
            # Skip frames to maintain target FPS
            for _ in range(self._skip_n - 1):
                self._cap.grab()
                self._frame_count += 1

            ret, frame = self._cap.read()
            self._frame_count += 1

            if not ret or frame is None:
                logger.warning("Failed to read frame from %s (frame #%d)", self.url, self._frame_count)
                return None

            return frame

        except cv2.error as exc:
            logger.error("OpenCV error reading frame from %s: %s", self.url, exc)
            return None

    def frames(self) -> Generator[np.ndarray, None, None]:
        """
        Generator yielding frames from the stream with automatic reconnection.
        """
        retries = 0
        while self._running:
            if not self.open():
                retries += 1
                if 0 < self.max_retries <= retries:
                    logger.error("Max retries (%d) exceeded for %s", self.max_retries, self.url)
                    break
                logger.info("Retrying RTSP connection in %.1fs (retry %d)...", self.reconnect_delay, retries)
                time.sleep(self.reconnect_delay)
                continue

            retries = 0  # Reset on successful connection
            while self._running:
                frame = self.read_frame()
                if frame is None:
                    logger.warning("Stream %s lost — will reconnect", self.url)
                    break
                yield frame

            self.release()
            if self._running:
                logger.info("Reconnecting to %s in %.1fs...", self.url, self.reconnect_delay)
                time.sleep(self.reconnect_delay)

    def release(self) -> None:
        """Release the video capture resource."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.debug("Released RTSP stream: %s", self.url)

    def stop(self) -> None:
        """Stop the stream reader."""
        self._running = False
        self.release()

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def is_running(self) -> bool:
        return self._running
